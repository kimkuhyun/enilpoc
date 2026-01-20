"""여행 시뮬레이션 MVP - Streamlit 앱."""

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
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 사용자 정의 CSS
st.markdown("""
    <style>
    .phone-screen {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 30px;
        padding: 30px 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 20px auto;
        max-width: 400px;
    }
    .notification-card {
        background: white;
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .notification-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    .notification-badge {
        background: #ff4444;
        color: white;
        border-radius: 50%;
        padding: 5px 10px;
        font-size: 12px;
        font-weight: bold;
    }
    .activity-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-active { background: #4CAF50; }
    .status-pending { background: #FFC107; }
    .status-completed { background: #9E9E9E; }
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


# 사이드바 - 설정 및 제어
with st.sidebar:
    st.title("🗺️ 여행 시뮬레이터")
    st.markdown("---")
    
    # API 키 설정
    st.subheader("⚙️ 설정")
    
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
    st.subheader("📋 여행 계획 관리")
    
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
    st.subheader("🔄 시뮬레이션 제어")
    
    if st.button("시뮬레이션 초기화"):
        st.session_state.simulator = TravelSimulator()
        st.session_state.chat_messages = []
        st.session_state.chat_open = False
        st.rerun()
    
    if st.button("알림 모두 삭제"):
        st.session_state.simulator.clear_notifications()
        st.rerun()


# 메인 콘텐츠
st.title("🗺️ AI 여행 시뮬레이터")

if not st.session_state.api_key_provided:
    st.warning("⚠️ 사이드바에서 API 키를 입력하여 시작하세요")
    st.stop()

# 탭 생성
tab1, tab2, tab3, tab4 = st.tabs(["📝 계획 생성", "🎮 시뮬레이션", "📱 핸드폰", "💬 챗봇"])

# 탭 1: 계획 생성
with tab1:
    st.header("여행 계획 생성")
    
    with st.form("plan_form"):
        st.write("여행 계획을 자유롭게 설명해주세요:")
        
        plan_input = st.text_area(
            "여행 계획",
            height=150,
            placeholder="예: 내일 서울에서 하루 여행을 계획하고 있어요. 아침에 경복궁을 방문하고, "
                       "점심은 명동에서 먹고, 오후에는 남산타워에 가고 싶어요. 저녁에는 홍대에서 식사하려고 해요."
        )
        
        submitted = st.form_submit_button("🚀 계획 생성")
        
        if submitted and plan_input:
            with st.spinner("AI가 계획을 생성하는 중..."):
                result = st.session_state.plan_generator.generate_structured_plan(plan_input)
                
                if "error" in result:
                    st.error(f"오류: {result['error']}")
                    if "raw_response" in result:
                        with st.expander("응답 확인"):
                            st.code(result["raw_response"])
                else:
                    st.success("✅ 계획이 생성되었습니다!")
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
                    st.success("✅ 계획이 수정되었습니다!")
                    st.json(result)
                    st.rerun()

# 탭 2: 시뮬레이션
with tab2:
    st.header("여행 시뮬레이션 제어판")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📍 위치 제어")
        
        # 위치 선택
        location_preset = st.selectbox(
            "빠른 위치 선택",
            ["직접 입력"] + list(SEOUL_LANDMARKS.keys())
        )
        
        if location_preset != "직접 입력":
            preset = SEOUL_LANDMARKS[location_preset]
            default_lat = preset["lat"]
            default_lon = preset["lon"]
            location_name = location_preset
        else:
            default_lat = st.session_state.simulator.state["location"]["latitude"]
            default_lon = st.session_state.simulator.state["location"]["longitude"]
            location_name = st.session_state.simulator.state["location"]["name"]
        
        # 위도/경도 슬라이더
        latitude = st.slider(
            "위도",
            min_value=37.4,
            max_value=37.7,
            value=default_lat,
            step=0.0001,
            format="%.4f"
        )
        
        longitude = st.slider(
            "경도",
            min_value=126.8,
            max_value=127.2,
            value=default_lon,
            step=0.0001,
            format="%.4f"
        )
        
        if location_preset == "직접 입력":
            location_name = st.text_input("위치 이름", value=location_name)
        
        if st.button("위치 업데이트"):
            st.session_state.simulator.update_location(latitude, longitude, location_name)
            st.success(f"위치가 {location_name}으로 업데이트되었습니다")
        
        # 현재 위치 표시
        st.info(f"현재 위치: {st.session_state.simulator.state['location']['name']}\n"
                f"위도: {st.session_state.simulator.state['location']['latitude']:.4f}, "
                f"경도: {st.session_state.simulator.state['location']['longitude']:.4f}")
    
    with col2:
        st.subheader("⏰ 시간 제어")
        
        # 날짜 선택
        current_dt = datetime.fromisoformat(st.session_state.simulator.state["datetime"])
        
        date_input = st.date_input("날짜", value=current_dt.date())
        time_input = st.time_input("시간", value=current_dt.time())
        
        if st.button("시간 업데이트"):
            new_dt = datetime.combine(date_input, time_input)
            st.session_state.simulator.update_datetime(new_dt.isoformat())
            st.success(f"시간이 업데이트되었습니다")
        
        # 빠른 시간 진행
        st.markdown("빠른 시간 진행:")
        col_t1, col_t2, col_t3 = st.columns(3)
        
        with col_t1:
            if st.button("+15분"):
                st.session_state.simulator.advance_time(15)
                st.rerun()
        
        with col_t2:
            if st.button("+1시간"):
                st.session_state.simulator.advance_time(60)
                st.rerun()
        
        with col_t3:
            if st.button("+3시간"):
                st.session_state.simulator.advance_time(180)
                st.rerun()
        
        # 현재 시간 표시
        time_info = st.session_state.simulator.get_current_time_info()
        st.info(f"현재 시간: {time_info['date']} {time_info['hour']:02d}:{time_info['minute']:02d}\n"
                f"시간대: {time_info['time_of_day']}, {time_info['day_of_week']}")
    
    st.markdown("---")
    
    # 날씨 제어
    st.subheader("🌤️ 날씨 제어")
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        weather = st.selectbox(
            "날씨 상태",
            ["맑음", "구름조금", "흐림", "비", "눈"],
            index=["맑음", "구름조금", "흐림", "비", "눈"].index(
                st.session_state.simulator.state["weather"]
            )
        )
    
    with col_w2:
        temperature = st.slider(
            "기온 (°C)",
            min_value=-10,
            max_value=40,
            value=st.session_state.simulator.state["temperature"],
            step=1
        )
    
    if st.button("날씨 업데이트"):
        st.session_state.simulator.update_weather(weather, temperature)
        st.success(f"날씨가 업데이트되었습니다: {weather}, {temperature}°C")
    
    st.info(f"현재 날씨: {st.session_state.simulator.state['weather']}, "
            f"{st.session_state.simulator.state['temperature']}°C")
    
    st.markdown("---")
    
    # 트리거 확인 버튼
    st.subheader("🔔 트리거 확인")
    
    if st.button("수동으로 트리거 확인", type="primary"):
        current_state = st.session_state.simulator.get_state()
        
        triggered = st.session_state.rag.check_triggers(
            current_location=current_state["location"],
            current_time=datetime.fromisoformat(current_state["datetime"]).strftime("%H:%M"),
            current_weather=current_state["weather"]
        )
        
        if triggered:
            st.success(f"🔔 {len(triggered)}개의 트리거가 활성화되었습니다!")
            
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
                
                with st.expander(f"📍 {activity.get('name')}"):
                    st.write(f"**위치**: {activity.get('location')}")
                    st.write(f"**메시지**: {trigger.get('message')}")
                    st.write(f"**트리거 타입**: {trigger.get('type')}")
        else:
            st.info("현재 활성화된 트리거가 없습니다")
    
    # 자동 트리거 확인 (주기적)
    if current_plan and (datetime.now() - st.session_state.last_trigger_check).seconds > 5:
        current_state = st.session_state.simulator.get_state()
        
        triggered = st.session_state.rag.check_triggers(
            current_location=current_state["location"],
            current_time=datetime.fromisoformat(current_state["datetime"]).strftime("%H:%M"),
            current_weather=current_state["weather"]
        )
        
        for t in triggered:
            activity = t["activity"]
            trigger = t["trigger"]
            
            # 중복 알림 방지
            existing_notifications = st.session_state.simulator.state["notifications"]
            is_duplicate = any(
                n.get("activity", {}).get("name") == activity.get("name") and
                not n.get("read", False)
                for n in existing_notifications
            )
            
            if not is_duplicate:
                notification = {
                    "type": trigger.get("type", "general"),
                    "title": activity.get("name", "알림"),
                    "message": trigger.get("message", "활동 알림"),
                    "activity": activity,
                    "trigger": trigger
                }
                st.session_state.simulator.add_notification(notification)
        
        st.session_state.last_trigger_check = datetime.now()


# 탭 3: 핸드폰 화면
with tab3:
    st.header("📱 모바일 화면")
    
    # 핸드폰 스타일 컨테이너
    st.markdown('<div class="phone-screen">', unsafe_allow_html=True)
    
    # 상태바
    col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
    with col_status1:
        time_info = st.session_state.simulator.get_current_time_info()
        st.markdown(f"**{time_info['hour']:02d}:{time_info['minute']:02d}**")
    with col_status2:
        st.markdown(f"**{st.session_state.simulator.state['location']['name']}**")
    with col_status3:
        unread = len(st.session_state.simulator.get_unread_notifications())
        if unread > 0:
            st.markdown(
                f'<span class="notification-badge">{unread}</span>',
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # 알림 목록
    notifications = st.session_state.simulator.state["notifications"]
    
    if not notifications:
        st.info("📭 알림이 없습니다")
    else:
        st.subheader(f"알림 ({len(notifications)})")
        
        for idx, notif in enumerate(reversed(notifications)):
            actual_idx = len(notifications) - 1 - idx
            
            is_read = notif.get("read", False)
            bg_color = "#f8f9fa" if is_read else "#ffffff"
            
            with st.container():
                st.markdown(
                    f'<div class="notification-card" style="background: {bg_color};">',
                    unsafe_allow_html=True
                )
                
                col_n1, col_n2 = st.columns([3, 1])
                
                with col_n1:
                    icon = "🔔" if not is_read else "✅"
                    st.markdown(f"### {icon} {notif.get('title', '알림')}")
                    st.write(notif.get("message", ""))
                    
                    if "activity" in notif:
                        activity = notif["activity"]
                        st.caption(f"📍 {activity.get('location', '')} | "
                                 f"⏰ {activity.get('time', '')} | "
                                 f"⏱️ {activity.get('duration_minutes', 0)}분")
                
                with col_n2:
                    if not is_read:
                        if st.button("읽음", key=f"read_{actual_idx}"):
                            st.session_state.simulator.mark_notification_read(actual_idx)
                            st.rerun()
                    
                    if st.button("챗봇", key=f"chat_{actual_idx}"):
                        st.session_state.chat_open = True
                        # 컨텍스트 메시지 추가
                        if "activity" in notif:
                            activity = notif["activity"]
                            context_msg = f"[알림] {activity.get('name')}: {notif.get('message')}"
                            
                            if not st.session_state.chat_messages or \
                               st.session_state.chat_messages[-1].get("content") != context_msg:
                                st.session_state.chat_messages.append({
                                    "role": "system",
                                    "content": context_msg
                                })
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("")
    
    st.markdown('</div>', unsafe_allow_html=True)


# 탭 4: 챗봇
with tab4:
    st.header("💬 AI 여행 도우미")
    
    if not st.session_state.chat_open:
        st.info("알림에서 '챗봇' 버튼을 눌러 대화를 시작하거나, 아래에서 직접 질문하세요.")
    
    # 현재 상태 표시
    with st.expander("📊 현재 상황"):
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
st.caption("🎮 여행 시뮬레이터 MVP - 실제 위치, 시간, 날씨를 조작하여 여행을 시뮬레이션하세요")
