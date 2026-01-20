"""여행 시뮬레이션 MVP - Streamlit 앱 (이모지 제거, 간소화)."""

import streamlit as st
from datetime import datetime, timedelta
import json

from agent.plan_generator import PlanGenerator
from agent.plan_rag import TravelPlanRAG
from agent.simulator import TravelSimulator, SEOUL_LANDMARKS
from agent.travel_agent import TravelAgent
from utils.config import config

# 페이지 설정
st.set_page_config(
    page_title="여행 시뮬레이터 AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 CSS
st.markdown("""
    <style>
    .notification-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .notification-card.unread {
        border-left: 4px solid #667eea;
        background: #f8f9ff;
    }
    .scenario-button {
        background: #667eea;
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        margin: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "simulator" not in st.session_state:
    st.session_state.simulator = TravelSimulator()

if "plan_generator" not in st.session_state:
    st.session_state.plan_generator = PlanGenerator()

if "rag" not in st.session_state:
    st.session_state.rag = TravelPlanRAG()

if "agent" not in st.session_state:
    st.session_state.agent = TravelAgent()

if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "api_key_provided" not in st.session_state:
    st.session_state.api_key_provided = config.is_configured()

if "last_trigger_check" not in st.session_state:
    st.session_state.last_trigger_check = datetime.now()

if "auto_play" not in st.session_state:
    st.session_state.auto_play = False


# 사이드바 - 설정 및 제어
with st.sidebar:
    st.title("여행 시뮬레이터")
    st.markdown("---")
    
    # API 키 설정
    st.subheader("설정")
    
    provider = st.selectbox(
        "LLM 제공자",
        ["openai", "anthropic", "upstage"],
        index=0 if config.LLM_PROVIDER == "openai" else 1 if config.LLM_PROVIDER == "anthropic" else 2
    )
    
    api_key_input = st.text_input(
        f"{provider.upper()} API 키",
        type="password",
        value="" if not config.is_configured() else "설정됨",
        help="API 키를 입력하거나 .env 파일에 설정하세요"
    )
    
    if api_key_input and api_key_input != "설정됨":
        if provider == "openai":
            config.OPENAI_API_KEY = api_key_input
        elif provider == "anthropic":
            config.ANTHROPIC_API_KEY = api_key_input
        else:
            config.UPSTAGE_API_KEY = api_key_input
        config.LLM_PROVIDER = provider
        
        st.session_state.plan_generator = PlanGenerator()
        st.session_state.agent = TravelAgent()
        st.session_state.api_key_provided = True
    
    st.markdown("---")
    
    # 계획 관리
    st.subheader("여행 계획 관리")
    
    current_plan = st.session_state.rag.get_current_plan()
    
    if current_plan:
        st.success(f"활성 계획: {current_plan.get('destination', '알 수 없음')}")
        
        with st.expander("계획 상세보기"):
            st.json(current_plan)
        
        if st.button("계획 초기화"):
            st.session_state.rag.plans = {"plans": [], "current_plan_id": None}
            st.session_state.rag._save_plans()
            st.rerun()
    else:
        st.info("생성된 계획이 없습니다")
    
    st.markdown("---")
    
    # 시뮬레이션 초기화
    st.subheader("시뮬레이션 제어")
    
    if st.button("시뮬레이션 초기화"):
        st.session_state.simulator = TravelSimulator()
        st.session_state.chat_messages = []
        st.session_state.chat_open = False
        st.rerun()
    
    if st.button("알림 모두 삭제"):
        st.session_state.simulator.clear_notifications()
        st.rerun()


# 메인 콘텐츠
st.title("AI 여행 시뮬레이터")

if not st.session_state.api_key_provided:
    st.warning("사이드바에서 API 키를 입력하여 시작하세요")
    st.stop()

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["계획 생성", "시뮬레이션", "핸드폰", "챗봇"])

# 탭 1: 계획 생성
with tab1:
    st.header("여행 계획 생성")
    
    with st.form("plan_form"):
        st.write("여행 계획을 자유롭게 설명해주세요:")
        
        plan_input = st.text_area(
            "여행 계획",
            height=150,
            placeholder="예: 내일 서울에서 하루 여행을 계획하고 있어요. 아침에 경복궁을 방문하고, "
                       "점심은 명동에서 먹고, 오후에는 남산타워에 가고 싶어요."
        )
        
        submitted = st.form_submit_button("계획 생성")
        
        if submitted and plan_input:
            with st.spinner("AI가 계획을 생성하는 중..."):
                result = st.session_state.plan_generator.generate_structured_plan(plan_input)
                
                if "error" in result:
                    st.error(f"오류: {result['error']}")
                    if "raw_response" in result:
                        with st.expander("응답 확인"):
                            st.code(result["raw_response"])
                else:
                    st.success("계획이 생성되었습니다!")
                    st.json(result)
    
    # 계획 수정
    if current_plan:
        st.markdown("---")
        st.subheader("계획 수정")
        
        modification = st.text_input(
            "수정 요청",
            placeholder="예: 경복궁 방문 시간을 오후로 변경해주세요"
        )
        
        if st.button("계획 수정하기") and modification:
            with st.spinner("계획을 수정하는 중..."):
                result = st.session_state.plan_generator.modify_plan(
                    current_plan["id"], 
                    modification
                )
                
                if "error" in result:
                    st.error(f"오류: {result['error']}")
                else:
                    st.success("계획이 수정되었습니다!")
                    st.json(result)
                    st.rerun()

# 탭 2: 시뮬레이션 (간소화)
with tab2:
    st.header("여행 시뮬레이션 제어판")
    
    # 빠른 시나리오 버튼
    st.subheader("빠른 시나리오")
    st.write("계획의 각 활동 위치로 바로 이동할 수 있습니다")
    
    if current_plan and current_plan.get("activities"):
        cols = st.columns(min(3, len(current_plan["activities"])))
        
        for idx, activity in enumerate(current_plan["activities"][:6]):  # 최대 6개만 표시
            col_idx = idx % 3
            with cols[col_idx]:
                if st.button(
                    f"{activity.get('name', '활동')}",
                    key=f"scenario_{idx}",
                    use_container_width=True
                ):
                    # 활동 위치로 이동
                    st.session_state.simulator.update_location(
                        activity.get("latitude", 37.5665),
                        activity.get("longitude", 126.9780),
                        activity.get("location", "위치")
                    )
                    
                    # 활동 시간으로 설정
                    if activity.get("time"):
                        time_str = activity.get("time")
                        hour, minute = map(int, time_str.split(":"))
                        dt = datetime.fromisoformat(st.session_state.simulator.state["datetime"])
                        new_dt = dt.replace(hour=hour, minute=minute)
                        st.session_state.simulator.update_datetime(new_dt.isoformat())
                    
                    st.rerun()
    else:
        st.info("계획을 먼저 생성하세요")
    
    st.markdown("---")
    
    # 자동 재생 모드
    st.subheader("자동 재생")
    
    col_auto1, col_auto2 = st.columns(2)
    
    with col_auto1:
        if st.button("계획 따라 자동 진행", use_container_width=True):
            if current_plan and current_plan.get("activities"):
                st.session_state.auto_play = True
                st.success("자동 재생 시작!")
            else:
                st.warning("계획이 없습니다")
    
    with col_auto2:
        if st.button("자동 재생 중지", use_container_width=True):
            st.session_state.auto_play = False
            st.info("자동 재생 중지")
    
    st.markdown("---")
    
    # 수동 제어 (간소화)
    st.subheader("수동 제어")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("**위치 제어**")
        
        # 위치 프리셋
        location_preset = st.selectbox(
            "빠른 위치 선택",
            ["현재 위치 유지"] + list(SEOUL_LANDMARKS.keys()),
            key="location_select"
        )
        
        if location_preset != "현재 위치 유지":
            if st.button("위치 이동", use_container_width=True):
                preset = SEOUL_LANDMARKS[location_preset]
                st.session_state.simulator.update_location(
                    preset["lat"],
                    preset["lon"],
                    location_preset
                )
                st.success(f"{location_preset}(으)로 이동")
                st.rerun()
        
        # 현재 위치 표시
        current_loc = st.session_state.simulator.state['location']
        st.caption(f"현재: {current_loc['name']}")
        st.caption(f"좌표: {current_loc['latitude']:.4f}, {current_loc['longitude']:.4f}")
    
    with col2:
        st.write("**시간 제어**")
        
        # 시간 빠른 진행
        time_cols = st.columns(3)
        with time_cols[0]:
            if st.button("+15분", use_container_width=True):
                st.session_state.simulator.advance_time(15)
                st.rerun()
        with time_cols[1]:
            if st.button("+1시간", use_container_width=True):
                st.session_state.simulator.advance_time(60)
                st.rerun()
        with time_cols[2]:
            if st.button("+3시간", use_container_width=True):
                st.session_state.simulator.advance_time(180)
                st.rerun()
        
        # 현재 시간 표시
        time_info = st.session_state.simulator.get_current_time_info()
        st.caption(f"현재: {time_info['date']} {time_info['hour']:02d}:{time_info['minute']:02d}")
        st.caption(f"시간대: {time_info['time_of_day']}")
    
    st.markdown("---")
    
    # 날씨 제어 (간소화)
    st.subheader("날씨 제어")
    
    col_w1, col_w2, col_w3 = st.columns(3)
    
    with col_w1:
        weather = st.selectbox(
            "날씨",
            ["맑음", "구름조금", "흐림", "비", "눈"]
        )
    
    with col_w2:
        temperature = st.number_input(
            "기온 (°C)",
            min_value=-10,
            max_value=40,
            value=st.session_state.simulator.state["temperature"],
            step=5
        )
    
    with col_w3:
        st.write("")  # 간격
        st.write("")
        if st.button("날씨 적용", use_container_width=True):
            st.session_state.simulator.update_weather(weather, temperature)
            st.success("날씨 업데이트")
            st.rerun()
    
    # 현재 날씨
    st.caption(f"현재 날씨: {st.session_state.simulator.state['weather']}, {st.session_state.simulator.state['temperature']}°C")
    
    st.markdown("---")
    
    # 트리거 확인
    st.subheader("트리거 확인")
    
    if st.button("지금 트리거 확인하기", type="primary", use_container_width=True):
        current_state = st.session_state.simulator.get_state()
        
        triggered = st.session_state.rag.check_triggers(
            current_location=current_state["location"],
            current_time=datetime.fromisoformat(current_state["datetime"]).strftime("%H:%M"),
            current_weather=current_state["weather"]
        )
        
        if triggered:
            st.success(f"{len(triggered)}개의 트리거 활성화!")
            
            for t in triggered:
                activity = t["activity"]
                trigger = t["trigger"]
                
                notification = {
                    "type": trigger.get("type", "general"),
                    "title": activity.get("name", "알림"),
                    "message": trigger.get("message", "활동 알림"),
                    "activity": activity,
                    "trigger": trigger
                }
                
                st.session_state.simulator.add_notification(notification)
                st.write(f"- {activity.get('name')}: {trigger.get('message')}")
        else:
            st.info("활성화된 트리거가 없습니다")


# 탭 3: 핸드폰 화면 (간소화)
with tab3:
    st.header("모바일 알림")
    
    # 현재 상태 표시
    time_info = st.session_state.simulator.get_current_time_info()
    location = st.session_state.simulator.state["location"]
    
    st.write(f"**시간:** {time_info['hour']:02d}:{time_info['minute']:02d} | "
             f"**위치:** {location['name']} | "
             f"**날씨:** {st.session_state.simulator.state['weather']} {st.session_state.simulator.state['temperature']}°C")
    
    st.markdown("---")
    
    # 알림 목록
    notifications = st.session_state.simulator.state["notifications"]
    unread_count = len([n for n in notifications if not n.get("read", False)])
    
    st.subheader(f"알림 ({len(notifications)}) | 읽지 않음: {unread_count}")
    
    if not notifications:
        st.info("알림이 없습니다")
    else:
        for idx, notif in enumerate(reversed(notifications)):
            actual_idx = len(notifications) - 1 - idx
            is_read = notif.get("read", False)
            
            # 알림 카드
            card_class = "notification-card" if is_read else "notification-card unread"
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            col_n1, col_n2 = st.columns([3, 1])
            
            with col_n1:
                status = "[읽음]" if is_read else "[새 알림]"
                st.markdown(f"### {status} {notif.get('title', '알림')}")
                st.write(notif.get("message", ""))
                
                if "activity" in notif:
                    activity = notif["activity"]
                    st.caption(f"위치: {activity.get('location', '')} | "
                             f"시간: {activity.get('time', '')} | "
                             f"소요: {activity.get('duration_minutes', 0)}분")
            
            with col_n2:
                if not is_read:
                    if st.button("읽음", key=f"read_{actual_idx}"):
                        st.session_state.simulator.mark_notification_read(actual_idx)
                        st.rerun()
                
                if st.button("챗봇", key=f"chat_{actual_idx}"):
                    st.session_state.chat_open = True
                    
                    # 컨텍스트 추가
                    if "activity" in notif:
                        activity = notif["activity"]
                        context_msg = f"[알림 선택] {activity.get('name')}: {notif.get('message')}"
                        
                        if not st.session_state.chat_messages or \
                           st.session_state.chat_messages[-1].get("content") != context_msg:
                            st.session_state.chat_messages.append({
                                "role": "system",
                                "content": context_msg
                            })
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.write("")  # 간격


# 탭 4: 챗봇
with tab4:
    st.header("AI 여행 도우미")
    
    if not st.session_state.chat_open:
        st.info("알림에서 '챗봇' 버튼을 누르거나 아래에서 직접 질문하세요.")
    
    # 현재 상황 표시
    with st.expander("현재 상황"):
        state = st.session_state.simulator.get_state()
        time_info = st.session_state.simulator.get_current_time_info()
        
        col_ctx1, col_ctx2, col_ctx3 = st.columns(3)
        
        with col_ctx1:
            st.metric("위치", state["location"]["name"])
            st.caption(f"{state['location']['latitude']:.4f}, {state['location']['longitude']:.4f}")
        
        with col_ctx2:
            st.metric("시간", f"{time_info['hour']:02d}:{time_info['minute']:02d}")
            st.caption(f"{time_info['time_of_day']}, {time_info['day_of_week']}")
        
        with col_ctx3:
            st.metric("날씨", state["weather"])
            st.caption(f"{state['temperature']}°C")
    
    # 채팅 메시지 표시
    for message in st.session_state.chat_messages:
        if message["role"] == "system":
            st.info(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # 채팅 입력
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 컨텍스트 추가
        state = st.session_state.simulator.get_state()
        time_info = st.session_state.simulator.get_current_time_info()
        
        context_prompt = f"""{prompt}

[현재 상황]
- 위치: {state['location']['name']} ({state['location']['latitude']:.4f}, {state['location']['longitude']:.4f})
- 시간: {time_info['date']} {time_info['hour']:02d}:{time_info['minute']:02d} ({time_info['time_of_day']})
- 날씨: {state['weather']}, {state['temperature']}°C
"""
        
        # 현재 계획 추가
        if current_plan:
            context_prompt += f"\n[현재 여행 계획]\n목적지: {current_plan.get('destination', '')}\n"
            activities_str = "\n".join([
                f"- {a['name']} ({a['location']}, {a['time']})"
                for a in current_plan.get("activities", [])[:5]
            ])
            context_prompt += f"활동:\n{activities_str}\n"
        
        # AI 응답
        with st.chat_message("assistant"):
            with st.spinner("생각하는 중..."):
                response = st.session_state.agent.chat(context_prompt)
                st.markdown(response)
        
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
    
    # 채팅 초기화
    if st.button("대화 초기화"):
        st.session_state.chat_messages = []
        st.session_state.agent.reset_conversation()
        st.session_state.chat_open = False
        st.rerun()


# 푸터
st.markdown("---")
st.caption("여행 시뮬레이터 MVP - 실시간 시뮬레이션 기능")
