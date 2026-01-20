"""여행 시뮬레이션 - 완전한 핸드폰 UI + 3D 캐릭터."""

import streamlit as st
from datetime import datetime, timedelta
import json
import time
import pydeck as pdk
import random
import base64

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

if "moving_to_next" not in st.session_state:
    st.session_state.moving_to_next = False


def create_phone_html(notifications, time_info, location):
    """진짜 HTML 핸드폰 UI 생성"""
    
    unread = [n for n in notifications if not n.get("read", False)]
    
    notif_html = ""
    for idx, notif in enumerate(reversed(notifications[-5:])):
        actual_idx = len(notifications) - 1 - idx
        is_read = notif.get("read", False)
        
        bg_color = "#f0f4ff" if not is_read else "#ffffff"
        border_color = "#4CAF50" if not is_read else "#667eea"
        status_icon = "🆕" if not is_read else ""
        
        btn_html = f'<button onclick="window.parent.postMessage({{type: \'confirm\', index: {actual_idx}}}, \'*\')" style="background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer; font-size: 13px;">✅ 확인</button>' if not is_read else ""
        
        notif_html += f'''
        <div style="background: {bg_color}; margin: 12px; border-radius: 15px; padding: 16px; 
                    box-shadow: 0 3px 10px rgba(0,0,0,0.08); border-left: 5px solid {border_color};">
            <div style="font-weight: 600; font-size: 15px; margin-bottom: 6px; color: #333;">
                {status_icon} {notif.get("title", "알림")}
            </div>
            <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
                {notif.get("message", "")}
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; color: #999;">🕐 {notif.get("time", "방금")}</span>
                {btn_html}
            </div>
        </div>
        '''
    
    if not notifications:
        notif_html = '''
        <div style="padding: 30px 20px; text-align: center; color: #666;">
            <p style="font-size: 48px; margin-bottom: 10px;">📱</p>
            <p style="font-size: 16px; font-weight: 500;">알림이 없습니다</p>
            <p style="font-size: 13px; color: #999; margin-top: 8px;">계획을 생성하고 자동 진행을 시작하세요</p>
        </div>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f5f5f5;
            }}
            .phone-screen {{
                background: #ffffff;
                height: 100vh;
                overflow-y: auto;
            }}
            .status-bar {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 15px;
                font-size: 13px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: sticky;
                top: 0;
                z-index: 100;
            }}
            .content {{
                padding: 10px;
            }}
            h3 {{
                color: #333;
                margin: 15px 12px 10px;
                font-size: 18px;
            }}
            .subtitle {{
                color: #999;
                font-size: 12px;
                margin: 0 12px 10px;
            }}
        </style>
        <script>
            // 확인 버튼 클릭 시 부모 창으로 메시지 전송
            window.addEventListener('message', function(event) {{
                console.log('Received message:', event.data);
            }});
        </script>
    </head>
    <body>
        <div class="phone-screen">
            <div class="status-bar">
                <span>⏰ {time_info['hour']:02d}:{time_info['minute']:02d}</span>
                <span>📍 {location['name']}</span>
                <span>🔋 100%</span>
            </div>
            <div class="content">
                <h3>🔔 알림</h3>
                <p class="subtitle">전체: {len(notifications)} | 새 알림: {len(unread)}</p>
                {notif_html}
            </div>
        </div>
    </body>
    </html>
    '''
    
    return html


def create_pydeck_map_with_character(current_location, plan=None, path=[]):
    """캐릭터 아이콘이 있는 지도"""
    
    view_state = pdk.ViewState(
        latitude=current_location["latitude"],
        longitude=current_location["longitude"],
        zoom=14,
        pitch=0
    )
    
    layers = []
    
    # 계획 활동 지점
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
                    pickable=True
                )
            )
    
    # 이동 경로
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
    
    # 현재 위치 - 캐릭터 (큰 원)
    current_data = [{
        "position": [current_location["longitude"], current_location["latitude"]],
        "color": [255, 50, 50, 255],
        "name": "🚶 현재 위치"
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
        st.warning("⚠️ 유효한 API 키를 입력하세요")
        
        provider = st.selectbox("LLM", ["openai", "anthropic", "upstage"])
        api_key = st.text_input(f"{provider.upper()} API 키", type="password")
        
        if st.button("설정", type="primary") and api_key:
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
                    try:
                        result = st.session_state.plan_generator.generate_structured_plan(plan_input)
                        if "error" not in result:
                            st.success("✅ 완료!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"오류: {result['error']}")
                    except Exception as e:
                        st.error(f"오류: {str(e)}")
    
    with col2:
        if st.session_state.rag.get_current_plan():
            if st.button("초기화", use_container_width=True):
                st.session_state.rag.plans = {"plans": [], "current_plan_id": None}
                st.session_state.rag._save_plans()
                st.session_state.movement_path = []
                st.session_state.current_activity_index = 0
                st.session_state.auto_playing = False
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
    
    deck_map = create_pydeck_map_with_character(
        current_state["location"],
        current_plan,
        st.session_state.movement_path
    )
    map_placeholder.pydeck_chart(deck_map, use_container_width=True)
    
    # 제어 패널
    st.markdown("### 🎮 제어")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        if st.button("▶️ 자동 진행", use_container_width=True, type="primary", disabled=st.session_state.auto_playing):
            if current_plan and current_plan.get("activities"):
                st.session_state.auto_playing = True
                st.session_state.current_activity_index = 0
                st.session_state.movement_path = []
                st.session_state.current_step = 0
                st.session_state.waiting_for_notification = False
                st.session_state.moving_to_next = False
                
                # 첫 번째 활동으로 이동
                activity = current_plan["activities"][0]
                target_lat = activity.get("latitude", 37.5665)
                target_lon = activity.get("longitude", 126.9780)
                
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
            st.session_state.moving_to_next = False
            st.rerun()

with col_right:
    st.subheader("📱 안드로이드 화면")
    
    # HTML 핸드폰 UI
    time_info = st.session_state.simulator.get_current_time_info()
    notifications = st.session_state.simulator.state["notifications"]
    
    phone_html = create_phone_html(notifications, time_info, current_state['location'])
    
    # iframe으로 표시
    st.components.v1.html(phone_html, height=700, scrolling=True)
    
    # 알림 확인 버튼 (streamlit 버튼)
    st.markdown("---")
    unread = [n for n in notifications if not n.get("read", False)]
    
    if unread and st.session_state.waiting_for_notification:
        st.warning("⚠️ 알림을 확인해주세요!")
        
        for idx, notif in enumerate(unread):
            actual_idx = notifications.index(notif)
            
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                st.write(f"**{notif.get('title')}**")
            with col_btn2:
                if st.button("✅", key=f"confirm_{actual_idx}"):
                    # 알림 읽음 처리
                    st.session_state.simulator.mark_notification_read(actual_idx)
                    st.session_state.waiting_for_notification = False
                    st.session_state.moving_to_next = True
                    st.rerun()

# 자동 진행 로직
if st.session_state.auto_playing:
    if not st.session_state.waiting_for_notification:
        if st.session_state.current_step < st.session_state.total_steps:
            # 이동 중
            step = st.session_state.movement_path[st.session_state.current_step]
            st.session_state.simulator.update_location(
                step["latitude"],
                step["longitude"],
                "이동 중"
            )
            
            st.session_state.current_step += 1
            
            time.sleep(0.2)
            st.rerun()
            
        else:
            # 목적지 도착
            if not st.session_state.moving_to_next:
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
                    st.rerun()
                
                # 알림이 없으면 바로 다음으로
                st.session_state.moving_to_next = True
                st.rerun()
            
            else:
                # 다음 활동으로 이동
                st.session_state.current_activity_index += 1
                st.session_state.moving_to_next = False
                
                if st.session_state.current_activity_index < len(current_plan["activities"]):
                    # 다음 활동 경로 생성
                    next_activity = current_plan["activities"][st.session_state.current_activity_index]
                    target_lat = next_activity.get("latitude", 37.5665)
                    target_lon = next_activity.get("longitude", 126.9780)
                    
                    path = st.session_state.simulator.simulate_movement(
                        target_lat, target_lon, steps=20
                    )
                    st.session_state.movement_path = path
                    st.session_state.total_steps = len(path)
                    st.session_state.current_step = 0
                    st.session_state.character_thought = f"{next_activity.get('name')}(으)로 이동 중..."
                    
                    st.rerun()
                else:
                    # 모든 활동 완료
                    st.session_state.auto_playing = False
                    st.session_state.character_thought = "모든 일정 완료! 🎉"
                    st.rerun()

st.markdown("---")
st.caption("🚶 실시간 여행 시뮬레이터")
