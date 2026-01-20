"""여행 시뮬레이션 - 부드러운 애니메이션 + 안드로이드 UI (수정)."""

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

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

if "total_steps" not in st.session_state:
    st.session_state.total_steps = 0

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
        zoom=14,
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
                "color": [33, 102, 172, 220]
            })
        
        if activity_data:
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=activity_data,
                    get_position="position",
                    get_color="color",
                    get_radius=150,
                    pickable=True,
                    auto_highlight=True
                )
            )
    
    # 이동 경로 (빨간 선)
    if len(path) > 1:
        path_data = []
        for i in range(len(path) - 1):
            path_data.append({
                "start": [path[i]["longitude"], path[i]["latitude"]],
                "end": [path[i+1]["longitude"], path[i+1]["latitude"]],
                "color": [255, 0, 0, 200]
            })
        
        if path_data:
            layers.append(
                pdk.Layer(
                    "LineLayer",
                    data=path_data,
                    get_source_position="start",
                    get_target_position="end",
                    get_color="color",
                    get_width=8
                )
            )
    
    # 현재 위치 (사람 - 큰 빨간 원)
    current_data = [{
        "position": [current_location["longitude"], current_location["latitude"]],
        "color": [255, 50, 50, 255],
        "name": "현재 위치"
    }]
    
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=current_data,
            get_position="position",
            get_color="color",
            get_radius=200,
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

current_plan = st.session_state.rag.get_current_plan()
current_state = st.session_state.simulator.get_state()

with col_left:
    st.subheader("🗺️ 실시간 지도")
    
    # 말풍선
    if st.session_state.waiting_for_notification:
        thought = "🔔 알림이 왔어! 확인해봐야겠다"
    elif st.session_state.auto_playing:
        thought = f"🚶 {st.session_state.character_thought}"
    else:
        thought = "여행 시작할 준비 완료! ✨"
    
    st.info(thought)
    
    # 지도 표시
    map_placeholder = st.empty()
    
    deck_map = create_pydeck_map(
        current_state["location"],
        current_plan,
        st.session_state.movement_path
    )
    map_placeholder.pydeck_chart(deck_map, use_container_width=True)
    
    # 제어 패널
    st.markdown("### 🎮 제어")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        if st.button("▶️ 자동 진행", use_container_width=True, type="primary"):
            if current_plan and current_plan.get("activities"):
                st.session_state.auto_playing = True
                st.session_state.current_activity_index = 0
                st.session_state.movement_path = []
                st.session_state.current_step = 0
                st.session_state.waiting_for_notification = False
                
                # 첫 번째 활동으로 이동
                activity = current_plan["activities"][0]
                target_lat = activity.get("latitude", 37.5665)
                target_lon = activity.get("longitude", 126.9780)
                
                # 경로 생성
                path = st.session_state.simulator.simulate_movement(
                    target_lat, target_lon, steps=20
                )
                st.session_state.movement_path = path
                st.session_state.total_steps = len(path)
                st.session_state.character_thought = f"{activity.get('name')}(으)로 이동 중..."
                
                st.rerun()
    
    with col_c2:
        if st.button("⏸️ 정지", use_container_width=True):
            st.session_state.auto_playing = False
            st.rerun()
    
    with col_c3:
        if st.button("🔄 초기화", use_container_width=True):
            st.session_state.movement_path = []
            st.session_state.current_activity_index = 0
            st.session_state.auto_playing = False
            st.session_state.waiting_for_notification = False
            st.session_state.current_step = 0
            st.rerun()

with col_right:
    st.subheader("📱 안드로이드 화면")
    
    # 안드로이드 스타일 컨테이너
    with st.container():
        # 상태바
        time_info = st.session_state.simulator.get_current_time_info()
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 12px; border-radius: 10px 10px 0 0;
                    display: flex; justify-content: space-between;'>
            <span>⏰ {time_info['hour']:02d}:{time_info['minute']:02d}</span>
            <span>📍 {current_state['location']['name']}</span>
            <span>🔋 100%</span>
        </div>
        """, unsafe_allow_html=True)
        
        # 알림 영역
        st.markdown("#### 🔔 알림")
        
        notifications = st.session_state.simulator.state["notifications"]
        unread = [n for n in notifications if not n.get("read", False)]
        
        st.caption(f"전체: {len(notifications)} | 새 알림: {len(unread)}")
        
        if not notifications:
            st.info("📱 알림이 없습니다\n\n계획을 생성하고 자동 진행을 시작하세요")
        else:
            for idx, notif in enumerate(reversed(notifications[-5:])):
                actual_idx = len(notifications) - 1 - idx
                is_read = notif.get("read", False)
                
                with st.container():
                    if not is_read:
                        st.success(f"🆕 **{notif.get('title')}**")
                    else:
                        st.info(f"**{notif.get('title')}**")
                    
                    st.write(notif.get("message"))
                    st.caption(f"🕐 {notif.get('time', '방금')}")
                    
                    if not is_read:
                        if st.button("✅ 확인", key=f"r{actual_idx}"):
                            st.session_state.simulator.mark_notification_read(actual_idx)
                            st.session_state.waiting_for_notification = False
                            st.rerun()
                    
                    st.markdown("---")
        
        # 알림 확인 대기 메시지
        if st.session_state.waiting_for_notification and unread:
            st.warning("⚠️ 알림을 확인해주세요!")

# 자동 진행 애니메이션 로직 (페이지 하단)
if st.session_state.auto_playing and not st.session_state.waiting_for_notification:
    if st.session_state.current_step < st.session_state.total_steps:
        # 현재 단계의 위치로 이동
        step = st.session_state.movement_path[st.session_state.current_step]
        st.session_state.simulator.update_location(
            step["latitude"],
            step["longitude"],
            "이동 중"
        )
        
        # 다음 단계로
        st.session_state.current_step += 1
        
        # 지도 업데이트
        time.sleep(0.2)  # 빨리감기 속도
        st.rerun()
        
    else:
        # 목적지 도착
        activity = current_plan["activities"][st.session_state.current_activity_index]
        
        # 시간 업데이트
        if activity.get("time"):
            time_str = activity.get("time")
            hour, minute = map(int, time_str.split(":"))
            dt = datetime.fromisoformat(st.session_state.simulator.state["datetime"])
            new_dt = dt.replace(hour=hour, minute=minute)
            st.session_state.simulator.update_datetime(new_dt.isoformat())
        
        # 트리거 확인
        triggered = st.session_state.rag.check_triggers(
            current_location=st.session_state.simulator.get_state()["location"],
            current_time=datetime.fromisoformat(st.session_state.simulator.state["datetime"]).strftime("%H:%M"),
            current_weather=st.session_state.simulator.get_state()["weather"]
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
            st.session_state.character_thought = "알림 확인 필요"
            st.rerun()
        
        # 다음 활동으로
        st.session_state.current_activity_index += 1
        
        if st.session_state.current_activity_index < len(current_plan["activities"]):
            # 다음 활동 경로 생성
            next_activity = current_plan["activities"][st.session_state.current_activity_index]
            target_lat = next_activity.get("latitude", 37.5665)
            target_lon = next_activity.get("longitude", 126.9780)
            
            path = st.session_state.simulator.simulate_movement(
                target_lat, target_lon, steps=20
            )
            st.session_state.movement_path.extend(path)
            st.session_state.total_steps = len(st.session_state.movement_path)
            st.session_state.character_thought = f"{next_activity.get('name')}(으)로 이동 중..."
            
            st.rerun()
        else:
            # 모든 활동 완료
            st.session_state.auto_playing = False
            st.session_state.character_thought = "모든 일정 완료! 🎉"
            st.rerun()

st.markdown("---")
st.caption("🚶 실시간 여행 시뮬레이터")
