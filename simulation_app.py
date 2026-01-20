"""여행 시뮬레이션 - 실시간 이동 애니메이션 + 안드로이드 UI."""

import streamlit as st
from datetime import datetime, timedelta
import json
import time
import pydeck as pdk
import random

from agent.plan_generator import PlanGenerator
from agent.plan_rag import TravelPlanRAG
from agent.simulator import TravelSimulator, SEOUL_LANDMARKS
from agent.travel_agent import TravelAgent
from utils.config import config

# 페이지 설정
st.set_page_config(
    page_title="여행 시뮬레이터",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS
st.markdown("""
    <style>
    .main { padding: 1rem; }
    
    /* 안드로이드 핸드폰 스타일 */
    .phone-frame {
        background: linear-gradient(145deg, #2a2a2a 0%, #1a1a1a 100%);
        border-radius: 40px;
        padding: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        border: 3px solid #3a3a3a;
    }
    
    .phone-screen {
        background: #ffffff;
        border-radius: 30px;
        overflow: hidden;
        min-height: 650px;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* 안드로이드 상태바 */
    .status-bar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px 15px;
        font-size: 13px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* 알림 카드 */
    .notif-card {
        background: white;
        margin: 12px;
        border-radius: 15px;
        padding: 16px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        border-left: 5px solid #667eea;
    }
    
    .notif-card.new {
        background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
        border-left: 5px solid #4CAF50;
        box-shadow: 0 4px 15px rgba(76,175,80,0.2);
    }
    
    .notif-title {
        font-weight: 600;
        font-size: 15px;
        margin-bottom: 6px;
        color: #333;
    }
    
    .notif-msg {
        font-size: 13px;
        color: #666;
        margin-bottom: 8px;
    }
    
    .notif-time {
        font-size: 11px;
        color: #999;
    }
    
    /* 말풍선 */
    .bubble {
        background: white;
        border-radius: 18px;
        padding: 12px 18px;
        margin: 12px 0;
        box-shadow: 0 3px 12px rgba(0,0,0,0.15);
        position: relative;
        display: inline-block;
        max-width: 350px;
        font-size: 15px;
        color: #333;
    }
    
    .bubble:after {
        content: '';
        position: absolute;
        bottom: -12px;
        left: 35px;
        width: 0;
        height: 0;
        border: 12px solid transparent;
        border-top-color: white;
        border-bottom: 0;
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

if "api_key_provided" not in st.session_state:
    st.session_state.api_key_provided = config.is_configured()

if "auto_playing" not in st.session_state:
    st.session_state.auto_playing = False

if "movement_path" not in st.session_state:
    st.session_state.movement_path = []

if "current_activity_index" not in st.session_state:
    st.session_state.current_activity_index = 0

if "character_thought" not in st.session_state:
    st.session_state.character_thought = "여행 준비 중..."

if "waiting_for_notification" not in st.session_state:
    st.session_state.waiting_for_notification = False


def create_pydeck_map(current_location, plan=None, path=[]):
    """pydeck 2D 지도 생성"""
    
    view_state = pdk.ViewState(
        latitude=current_location["latitude"],
        longitude=current_location["longitude"],
        zoom=13,
        pitch=0
    )
    
    layers = []
    
    # 계획 활동 지점 (파란 원)
    if plan and plan.get("activities"):
        activities = plan["activities"]
        activity_data = []
        
        for act in activities:
            activity_data.append({
                "position": [act.get("longitude", 126.9780), act.get("latitude", 37.5665)],
                "name": act.get("name", "활동"),
                "color": [33, 102, 172, 200]
            })
        
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=activity_data,
                get_position="position",
                get_color="color",
                get_radius=120,
                pickable=True
            )
        )
    
    # 이동 경로 (빨간 선)
    if len(path) > 1:
        path_data = []
        for i in range(len(path) - 1):
            path_data.append({
                "start": [path[i]["longitude"], path[i]["latitude"]],
                "end": [path[i+1]["longitude"], path[i+1]["latitude"]],
                "color": [255, 0, 0, 180]
            })
        
        layers.append(
            pdk.Layer(
                "LineLayer",
                data=path_data,
                get_source_position="start",
                get_target_position="end",
                get_color="color",
                get_width=6
            )
        )
    
    # 현재 위치 (사람 - 큰 빨간 원)
    current_data = [{
        "position": [current_location["longitude"], current_location["latitude"]],
        "color": [255, 50, 50, 255]
    }]
    
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=current_data,
            get_position="position",
            get_color="color",
            get_radius=100,
            pickable=True
        )
    )
    
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=None,
        tooltip={"text": "{name}"}
    )
    
    return deck


def get_character_thought(state, current_plan):
    """캐릭터의 현재 생각"""
    
    if st.session_state.waiting_for_notification:
        return "🔔 알림이 왔어! 확인해봐야겠다"
    
    if st.session_state.auto_playing:
        if current_plan and current_plan.get("activities"):
            idx = st.session_state.current_activity_index
            if idx < len(current_plan["activities"]):
                activity = current_plan["activities"][idx]
                return f"🚶 {activity.get('name', '목적지')}(으)로 가는 중..."
    
    thoughts = [
        "오늘 날씨 좋네! ☀️",
        "어디로 갈까? 🤔",
        "배고픈데 뭐 먹지? 🍔",
        "사진 찍기 좋은 곳이네 📸",
        "잠깐 쉬어갈까? ☕"
    ]
    
    return random.choice(thoughts)


def auto_move_with_animation():
    """자동 진행 - 실시간 애니메이션"""
    current_plan = st.session_state.rag.get_current_plan()
    
    if not current_plan or not current_plan.get("activities"):
        st.session_state.auto_playing = False
        return False
    
    activities = current_plan["activities"]
    
    if st.session_state.current_activity_index >= len(activities):
        st.session_state.auto_playing = False
        st.session_state.current_activity_index = 0
        st.session_state.character_thought = "모든 일정 완료! 🎉"
        return False
    
    activity = activities[st.session_state.current_activity_index]
    
    # 목표 위치
    target_lat = activity.get("latitude", 37.5665)
    target_lon = activity.get("longitude", 126.9780)
    
    # 이동 경로 생성 (15단계로 부드럽게)
    path = st.session_state.simulator.simulate_movement(
        target_lat, target_lon, steps=15
    )
    
    st.session_state.character_thought = f"🚶 {activity.get('name')}(으)로 이동 중..."
    
    # 실시간 이동 애니메이션
    for i, step in enumerate(path):
        st.session_state.simulator.update_location(
            step["latitude"],
            step["longitude"],
            f"이동 중"
        )
        st.session_state.movement_path.append(step)
        
        # 지도 업데이트 (매 프레임)
        time.sleep(0.15)  # 빨리감기 속도
        
        # 진행 상황 표시
        if i % 3 == 0:  # 3 프레임마다 업데이트
            st.rerun()
    
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
    
    # 트리거 확인
    current_state = st.session_state.simulator.get_state()
    triggered = st.session_state.rag.check_triggers(
        current_location=current_state["location"],
        current_time=datetime.fromisoformat(current_state["datetime"]).strftime("%H:%M"),
        current_weather=current_state["weather"]
    )
    
    # 알림 생성
    if triggered:
        for t in triggered:
            act = t["activity"]
            trig = t["trigger"]
            
            notification = {
                "type": trig.get("type", "general"),
                "title": act.get("name", "알림"),
                "message": trig.get("message", "활동 알림"),
                "activity": act,
                "trigger": trig,
                "time": datetime.now().strftime("%H:%M")
            }
            st.session_state.simulator.add_notification(notification)
        
        # 알림 확인 대기
        st.session_state.waiting_for_notification = True
        st.session_state.character_thought = "🔔 알림이 왔다!"
        return True
    
    # 다음 활동으로
    st.session_state.current_activity_index += 1
    return False


# 메인 UI
st.title("🗺️ AI 여행 시뮬레이터")

# API 키 확인
if not st.session_state.api_key_provided:
    with st.expander("⚙️ API 키 설정", expanded=True):
        provider = st.selectbox("LLM", ["openai", "anthropic", "upstage"])
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

# 계획 생성
with st.expander("📝 여행 계획 생성", expanded=False):
    plan_input = st.text_area(
        "계획 입력",
        height=80,
        placeholder="예: 서울 하루 여행. 오전 경복궁 관람, 점심 북촌 한식당, 오후 인사동 쇼핑, 저녁 명동 맛집"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("생성", use_container_width=True, type="primary"):
            if plan_input:
                with st.spinner("계획 생성 중..."):
                    result = st.session_state.plan_generator.generate_structured_plan(plan_input)
                    if "error" not in result:
                        st.success("✅ 완료!")
                        st.rerun()
    
    with col2:
        if st.session_state.rag.get_current_plan():
            if st.button("초기화", use_container_width=True):
                st.session_state.rag.plans = {"plans": [], "current_plan_id": None}
                st.session_state.rag._save_plans()
                st.session_state.movement_path = []
                st.session_state.current_activity_index = 0
                st.rerun()

st.markdown("---")

# 분할 레이아웃
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🗺️ 실시간 지도")
    
    current_plan = st.session_state.rag.get_current_plan()
    current_state = st.session_state.simulator.get_state()
    
    # 말풍선
    thought = get_character_thought(current_state, current_plan)
    st.markdown(f'<div class="bubble">{thought}</div>', unsafe_allow_html=True)
    
    # 지도 표시 (st.empty()로 실시간 업데이트)
    map_placeholder = st.empty()
    
    deck_map = create_pydeck_map(
        current_state["location"],
        current_plan,
        st.session_state.movement_path
    )
    map_placeholder.pydeck_chart(deck_map)
    
    # 제어 패널
    st.markdown("### 🎮 제어")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        if st.button("▶️ 자동 진행", use_container_width=True, type="primary", disabled=st.session_state.auto_playing):
            if current_plan:
                st.session_state.auto_playing = True
                st.session_state.current_activity_index = 0
                st.session_state.movement_path = []
                st.session_state.waiting_for_notification = False
                st.rerun()
    
    with col_c2:
        if st.button("⏭️ 다음 단계", use_container_width=True):
            if current_plan:
                auto_move_with_animation()
                st.rerun()
    
    with col_c3:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.movement_path = []
            st.session_state.current_activity_index = 0
            st.session_state.auto_playing = False
            st.session_state.waiting_for_notification = False
            st.rerun()
    
    # 자동 진행 로직
    if st.session_state.auto_playing and not st.session_state.waiting_for_notification:
        need_check = auto_move_with_animation()
        if need_check:
            st.rerun()


with col_right:
    st.subheader("📱 안드로이드 화면")
    
    # 안드로이드 핸드폰
    st.markdown('<div class="phone-frame">', unsafe_allow_html=True)
    st.markdown('<div class="phone-screen">', unsafe_allow_html=True)
    
    # 상태바
    time_info = st.session_state.simulator.get_current_time_info()
    st.markdown(f"""
    <div class="status-bar">
        <span>⏰ {time_info['hour']:02d}:{time_info['minute']:02d}</span>
        <span>📍 {current_state['location']['name']}</span>
        <span>🔋 100%</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 알림 목록
    notifications = st.session_state.simulator.state["notifications"]
    unread = [n for n in notifications if not n.get("read", False)]
    
    st.markdown(f"### 🔔 알림 ({len(unread)} / {len(notifications)})")
    st.markdown("")
    
    if not notifications:
        st.markdown("""
        <div style="padding: 30px 20px; text-align: center; color: #666;">
            <p style="font-size: 48px; margin-bottom: 10px;">📱</p>
            <p style="font-size: 16px; font-weight: 500;">알림이 없습니다</p>
            <p style="font-size: 13px; color: #999; margin-top: 8px;">계획을 생성하고 자동 진행을 시작하세요</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for idx, notif in enumerate(reversed(notifications[-5:])):
            actual_idx = len(notifications) - 1 - idx
            is_read = notif.get("read", False)
            
            card_class = "notif-card" if is_read else "notif-card new"
            
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            col_n1, col_n2 = st.columns([3, 1])
            
            with col_n1:
                status = "" if is_read else "🆕 "
                st.markdown(f'<div class="notif-title">{status}{notif.get("title")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="notif-msg">{notif.get("message")}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="notif-time">🕐 {notif.get("time", "방금")}</div>', unsafe_allow_html=True)
            
            with col_n2:
                if not is_read:
                    if st.button("✅", key=f"r{actual_idx}", help="확인"):
                        st.session_state.simulator.mark_notification_read(actual_idx)
                        st.session_state.waiting_for_notification = False
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 알림 확인 대기 메시지
    if st.session_state.waiting_for_notification and unread:
        st.warning("⚠️ 알림을 확인해주세요!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.caption("🚶 실시간 여행 시뮬레이터 - 지도에서 이동 경로 확인")
