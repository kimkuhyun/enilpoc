"""여행 시뮬레이션 MVP - 지도 시각화 버전."""

import streamlit as st
from datetime import datetime, timedelta
import json
import time
import plotly.graph_objects as go

from agent.plan_generator import PlanGenerator
from agent.plan_rag import TravelPlanRAG
from agent.simulator import TravelSimulator, SEOUL_LANDMARKS
from agent.travel_agent import TravelAgent
from utils.config import config

# 페이지 설정
st.set_page_config(
    page_title="여행 시뮬레이터 AI",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .notification-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
    }
    .notification-card.unread {
        border-left: 4px solid #667eea;
        background: #f8f9ff;
    }
    .phone-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 30px;
        padding: 20px;
        min-height: 600px;
    }
    .phone-header {
        color: white;
        text-align: center;
        margin-bottom: 15px;
    }
    .control-button {
        width: 100%;
        margin: 5px 0;
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

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "api_key_provided" not in st.session_state:
    st.session_state.api_key_provided = config.is_configured()

if "auto_playing" not in st.session_state:
    st.session_state.auto_playing = False

if "movement_path" not in st.session_state:
    st.session_state.movement_path = []

if "current_activity_index" not in st.session_state:
    st.session_state.current_activity_index = 0


def create_map(current_location, plan=None, path=[]):
    """3D 지도 생성 (Plotly)"""
    
    fig = go.Figure()
    
    # 계획의 모든 활동 위치 표시
    if plan and plan.get("activities"):
        activities = plan["activities"]
        
        lats = [a.get("latitude", 37.5665) for a in activities]
        lons = [a.get("longitude", 126.9780) for a in activities]
        names = [a.get("name", "활동") for a in activities]
        
        # 활동 지점 표시
        fig.add_trace(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers+text',
            marker=dict(size=15, color='blue'),
            text=names,
            textposition="top center",
            name='계획 활동'
        ))
    
    # 이동 경로 표시
    if path:
        path_lats = [p["latitude"] for p in path]
        path_lons = [p["longitude"] for p in path]
        
        fig.add_trace(go.Scattermapbox(
            lat=path_lats,
            lon=path_lons,
            mode='lines',
            line=dict(width=3, color='red'),
            name='이동 경로'
        ))
    
    # 현재 위치 표시
    fig.add_trace(go.Scattermapbox(
        lat=[current_location["latitude"]],
        lon=[current_location["longitude"]],
        mode='markers',
        marker=dict(size=20, color='red', symbol='circle'),
        text=[current_location["name"]],
        name='현재 위치'
    ))
    
    # 지도 레이아웃
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(
                lat=current_location["latitude"],
                lon=current_location["longitude"]
            ),
            zoom=12,
            pitch=45  # 3D 각도
        ),
        height=600,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True
    )
    
    return fig


def auto_move_to_next_activity():
    """계획의 다음 활동으로 자동 이동"""
    current_plan = st.session_state.rag.get_current_plan()
    
    if not current_plan or not current_plan.get("activities"):
        st.session_state.auto_playing = False
        return
    
    activities = current_plan["activities"]
    
    if st.session_state.current_activity_index >= len(activities):
        st.session_state.auto_playing = False
        st.session_state.current_activity_index = 0
        st.success("모든 활동 완료!")
        return
    
    activity = activities[st.session_state.current_activity_index]
    
    # 현재 위치
    current_loc = st.session_state.simulator.state["location"]
    target_lat = activity.get("latitude", 37.5665)
    target_lon = activity.get("longitude", 126.9780)
    
    # 이동 경로 생성 (10단계)
    path = st.session_state.simulator.simulate_movement(
        target_lat, target_lon, steps=10
    )
    
    # 경로를 따라 이동 (애니메이션)
    for step in path:
        st.session_state.simulator.update_location(
            step["latitude"],
            step["longitude"],
            f"이동 중 ({step['step']}/{step['total_steps']})"
        )
        st.session_state.movement_path.append(step)
        time.sleep(0.3)  # 0.3초 간격
    
    # 목적지 도착
    st.session_state.simulator.update_location(
        target_lat,
        target_lon,
        activity.get("location", "목적지")
    )
    
    # 시간 업데이트
    if activity.get("time"):
        time_str = activity.get("time")
        hour, minute = map(int, time_str.split(":"))
        dt = datetime.fromisoformat(st.session_state.simulator.state["datetime"])
        new_dt = dt.replace(hour=hour, minute=minute)
        st.session_state.simulator.update_datetime(new_dt.isoformat())
    
    # 트리거 확인 및 알림 생성
    current_state = st.session_state.simulator.get_state()
    triggered = st.session_state.rag.check_triggers(
        current_location=current_state["location"],
        current_time=datetime.fromisoformat(current_state["datetime"]).strftime("%H:%M"),
        current_weather=current_state["weather"]
    )
    
    for t in triggered:
        act = t["activity"]
        trig = t["trigger"]
        
        notification = {
            "type": trig.get("type", "general"),
            "title": act.get("name", "알림"),
            "message": trig.get("message", "활동 알림"),
            "activity": act,
            "trigger": trig
        }
        st.session_state.simulator.add_notification(notification)
    
    # 다음 활동으로
    st.session_state.current_activity_index += 1


# 메인 UI
st.title("AI 여행 시뮬레이터 - 실시간 지도")

# API 키 확인
if not st.session_state.api_key_provided:
    with st.expander("API 키 설정", expanded=True):
        provider = st.selectbox("LLM 제공자", ["openai", "anthropic", "upstage"])
        api_key = st.text_input(f"{provider.upper()} API 키", type="password")
        
        if st.button("설정") and api_key:
            if provider == "openai":
                config.OPENAI_API_KEY = api_key
            elif provider == "anthropic":
                config.ANTHROPIC_API_KEY = api_key
            else:
                config.UPSTAGE_API_KEY = api_key
            config.LLM_PROVIDER = provider
            
            st.session_state.plan_generator = PlanGenerator()
            st.session_state.agent = TravelAgent()
            st.session_state.api_key_provided = True
            st.rerun()
    st.stop()

# 계획 생성 영역 (상단)
with st.expander("여행 계획 생성", expanded=False):
    plan_input = st.text_area(
        "여행 계획 입력",
        height=100,
        placeholder="예: 내일 서울에서 하루 여행. 아침 경복궁, 점심 명동, 오후 남산타워"
    )
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("계획 생성", use_container_width=True):
            if plan_input:
                with st.spinner("생성 중..."):
                    result = st.session_state.plan_generator.generate_structured_plan(plan_input)
                    if "error" in result:
                        st.error(f"오류: {result['error']}")
                    else:
                        st.success("계획 생성 완료!")
                        st.rerun()
    
    with col_p2:
        current_plan = st.session_state.rag.get_current_plan()
        if current_plan and st.button("계획 초기화", use_container_width=True):
            st.session_state.rag.plans = {"plans": [], "current_plan_id": None}
            st.session_state.rag._save_plans()
            st.rerun()

st.markdown("---")

# 메인 레이아웃: 왼쪽(지도+컨트롤) / 오른쪽(핸드폰)
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("실시간 지도 & 시뮬레이션")
    
    # 현재 상태
    current_plan = st.session_state.rag.get_current_plan()
    current_state = st.session_state.simulator.get_state()
    
    # 지도 표시
    map_fig = create_map(
        current_state["location"],
        current_plan,
        st.session_state.movement_path
    )
    st.plotly_chart(map_fig, use_container_width=True)
    
    # 제어 패널
    st.markdown("### 제어 패널")
    
    # 자동 진행
    col_auto1, col_auto2, col_auto3 = st.columns(3)
    
    with col_auto1:
        if st.button("자동 진행 시작", use_container_width=True, type="primary"):
            if current_plan and current_plan.get("activities"):
                st.session_state.auto_playing = True
                st.session_state.current_activity_index = 0
                st.session_state.movement_path = []
                st.info("자동 진행 시작! 계획의 각 지점으로 순차 이동합니다.")
    
    with col_auto2:
        if st.button("다음 활동으로", use_container_width=True):
            if current_plan and current_plan.get("activities"):
                auto_move_to_next_activity()
                st.rerun()
    
    with col_auto3:
        if st.button("경로 초기화", use_container_width=True):
            st.session_state.movement_path = []
            st.session_state.current_activity_index = 0
            st.session_state.auto_playing = False
            st.rerun()
    
    # 자동 진행 중일 때
    if st.session_state.auto_playing:
        with st.spinner("자동 진행 중..."):
            auto_move_to_next_activity()
            time.sleep(0.5)
            st.rerun()
    
    st.markdown("---")
    
    # 빠른 시나리오
    if current_plan and current_plan.get("activities"):
        st.markdown("### 빠른 이동")
        activities = current_plan["activities"]
        
        cols = st.columns(min(3, len(activities)))
        for idx, activity in enumerate(activities[:6]):
            col_idx = idx % 3
            with cols[col_idx]:
                if st.button(
                    activity.get("name", "활동"),
                    key=f"quick_{idx}",
                    use_container_width=True
                ):
                    # 즉시 이동
                    st.session_state.simulator.update_location(
                        activity.get("latitude", 37.5665),
                        activity.get("longitude", 126.9780),
                        activity.get("location", "위치")
                    )
                    
                    if activity.get("time"):
                        time_str = activity.get("time")
                        hour, minute = map(int, time_str.split(":"))
                        dt = datetime.fromisoformat(st.session_state.simulator.state["datetime"])
                        new_dt = dt.replace(hour=hour, minute=minute)
                        st.session_state.simulator.update_datetime(new_dt.isoformat())
                    
                    st.rerun()
    
    st.markdown("---")
    
    # 수동 제어
    st.markdown("### 수동 제어")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        st.write("**시간**")
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
        
        time_info = st.session_state.simulator.get_current_time_info()
        st.caption(f"{time_info['date']} {time_info['hour']:02d}:{time_info['minute']:02d}")
    
    with col_m2:
        st.write("**위치**")
        location_select = st.selectbox(
            "선택",
            ["현재"] + list(SEOUL_LANDMARKS.keys()),
            label_visibility="collapsed"
        )
        
        if location_select != "현재":
            if st.button("이동", use_container_width=True):
                preset = SEOUL_LANDMARKS[location_select]
                st.session_state.simulator.update_location(
                    preset["lat"], preset["lon"], location_select
                )
                st.rerun()
        
        st.caption(f"{current_state['location']['name']}")
    
    with col_m3:
        st.write("**날씨**")
        weather = st.selectbox(
            "선택",
            ["맑음", "흐림", "비", "눈"],
            label_visibility="collapsed"
        )
        
        if st.button("변경", use_container_width=True):
            st.session_state.simulator.update_weather(weather, 15)
            st.rerun()
        
        st.caption(f"{current_state['weather']} {current_state['temperature']}°C")
    
    # 트리거 확인
    if st.button("트리거 확인", use_container_width=True, type="secondary"):
        triggered = st.session_state.rag.check_triggers(
            current_location=current_state["location"],
            current_time=datetime.fromisoformat(current_state["datetime"]).strftime("%H:%M"),
            current_weather=current_state["weather"]
        )
        
        if triggered:
            for t in triggered:
                act = t["activity"]
                trig = t["trigger"]
                
                notification = {
                    "type": trig.get("type", "general"),
                    "title": act.get("name", "알림"),
                    "message": trig.get("message", "활동 알림"),
                    "activity": act,
                    "trigger": trig
                }
                st.session_state.simulator.add_notification(notification)
            
            st.success(f"{len(triggered)}개 알림 생성")
            st.rerun()


with col_right:
    st.subheader("모바일 알림")
    
    # 핸드폰 스타일 컨테이너
    st.markdown('<div class="phone-container">', unsafe_allow_html=True)
    
    # 상태바
    time_info = st.session_state.simulator.get_current_time_info()
    location = current_state["location"]
    
    st.markdown(f'<div class="phone-header">', unsafe_allow_html=True)
    st.markdown(f"**{time_info['hour']:02d}:{time_info['minute']:02d}** | "
                f"**{location['name']}** | "
                f"**{current_state['weather']} {current_state['temperature']}°C**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 알림 목록
    notifications = st.session_state.simulator.state["notifications"]
    unread = [n for n in notifications if not n.get("read", False)]
    
    st.markdown(f"### 알림 ({len(unread)} / {len(notifications)})")
    
    if not notifications:
        st.info("알림이 없습니다")
    else:
        # 알림 표시 (최신순)
        for idx, notif in enumerate(reversed(notifications[-10:])):  # 최근 10개만
            actual_idx = len(notifications) - 1 - idx
            is_read = notif.get("read", False)
            
            card_class = "notification-card" if is_read else "notification-card unread"
            
            with st.container():
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                
                col_n1, col_n2 = st.columns([3, 1])
                
                with col_n1:
                    status = "[읽음]" if is_read else "[NEW]"
                    st.markdown(f"**{status} {notif.get('title', '알림')}**")
                    st.caption(notif.get("message", ""))
                    
                    if "activity" in notif:
                        act = notif["activity"]
                        st.caption(f"{act.get('location')} | {act.get('time')}")
                
                with col_n2:
                    if not is_read:
                        if st.button("읽음", key=f"r_{actual_idx}"):
                            st.session_state.simulator.mark_notification_read(actual_idx)
                            st.rerun()
                    
                    if st.button("챗봇", key=f"c_{actual_idx}"):
                        if "activity" in notif:
                            act = notif["activity"]
                            context_msg = f"[알림] {act.get('name')}: {notif.get('message')}"
                            
                            if not st.session_state.chat_messages or \
                               st.session_state.chat_messages[-1].get("content") != context_msg:
                                st.session_state.chat_messages.append({
                                    "role": "system",
                                    "content": context_msg
                                })
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.write("")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 챗봇 (하단)
    st.markdown("---")
    st.markdown("### AI 챗봇")
    
    # 간단한 채팅 (3개만 표시)
    for message in st.session_state.chat_messages[-3:]:
        if message["role"] == "system":
            st.info(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.write(message["content"][:100] + "..." if len(message["content"]) > 100 else message["content"])
    
    # 채팅 입력
    if prompt := st.chat_input("질문 입력"):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # 컨텍스트 추가
        context_prompt = f"""{prompt}

[상황]
- 위치: {current_state['location']['name']}
- 시간: {time_info['hour']:02d}:{time_info['minute']:02d}
- 날씨: {current_state['weather']}
"""
        
        if current_plan:
            context_prompt += f"\n계획: {current_plan.get('destination', '')}"
        
        response = st.session_state.agent.chat(context_prompt)
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        
        st.rerun()

# 푸터
st.markdown("---")
st.caption("실시간 지도 시뮬레이션 - 계획에 따라 자동으로 이동하며 알림을 받습니다")
