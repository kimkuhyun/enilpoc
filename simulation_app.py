"""여행 시뮬레이터 - 완전한 버전 (알림 버그 수정 + 진짜 핸드폰 UI + 걷는 캐릭터)."""

import streamlit as st
from datetime import datetime, timedelta
import json
import time
import pydeck as pdk
import random

from agent.plan_generator import PlanGenerator
from agent.plan_rag import TravelPlanRAG
from agent.simulator import TravelSimulator
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

if "notification_to_confirm" not in st.session_state:
    st.session_state.notification_to_confirm = None


def create_phone_html_component(notifications, time_info, location):
    """진짜 안드로이드 핸드폰 HTML 컴포넌트"""
    
    unread = [n for n in notifications if not n.get("read", False)]
    
    # 알림 카드 HTML 생성
    notif_html = ""
    for idx, notif in enumerate(reversed(notifications[-5:])):
        actual_idx = len(notifications) - 1 - idx
        is_read = notif.get("read", False)
        
        bg_color = "linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%)" if not is_read else "#ffffff"
        border_color = "#4CAF50" if not is_read else "#ddd"
        status = "🆕 " if not is_read else ""
        
        notif_html += f'''
        <div style="background: {bg_color}; margin: 12px; border-radius: 15px; padding: 16px; 
                    box-shadow: 0 3px 10px rgba(0,0,0,0.08); border-left: 5px solid {border_color};">
            <div style="font-weight: 600; font-size: 15px; margin-bottom: 6px; color: #333;">
                {status}{notif.get("title", "알림")}
            </div>
            <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
                {notif.get("message", "")}
            </div>
            <div style="font-size: 11px; color: #999;">
                🕐 {notif.get("time", "방금")}
            </div>
        </div>
        '''
    
    if not notifications:
        notif_html = '''
        <div style="padding: 50px 20px; text-align: center; color: #999;">
            <p style="font-size: 60px; margin: 0;">📱</p>
            <p style="font-size: 18px; font-weight: 500; margin: 15px 0 5px;">알림이 없습니다</p>
            <p style="font-size: 14px;">계획을 생성하고 자동 진행을 시작하세요</p>
        </div>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                background: linear-gradient(145deg, #2a2a2a 0%, #1a1a1a 100%);
                padding: 20px;
                min-height: 100vh;
            }}
            .phone-frame {{
                background: #ffffff;
                border-radius: 40px;
                overflow: hidden;
                max-width: 380px;
                margin: 0 auto;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5), inset 0 0 20px rgba(0,0,0,0.1);
                border: 8px solid #2a2a2a;
            }}
            .status-bar {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 15px;
                font-size: 13px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-weight: 500;
            }}
            .content {{
                background: #f8f9fa;
                min-height: 600px;
                padding: 10px 0;
            }}
            h3 {{
                color: #333;
                margin: 15px 15px 5px;
                font-size: 20px;
            }}
            .subtitle {{
                color: #999;
                font-size: 12px;
                margin: 0 15px 10px;
            }}
        </style>
    </head>
    <body>
        <div class="phone-frame">
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


def create_map_with_walking_character(current_location, plan=None, path=[]):
    """걷는 캐릭터가 있는 지도 (IconLayer 사용)"""
    
    view_state = pdk.ViewState(
        latitude=current_location["latitude"],
        longitude=current_location["longitude"],
        zoom=14,
        pitch=0
    )
    
    layers = []
    
    # 활동 지점 (파란 원)
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
    
    # 현재 위치 - 걷는 사람 (큰 빨간 원)
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

# API 키 확인 (또는 샘플 계획 사용)
current_plan = st.session_state.rag.get_current_plan()

if not st.session_state.api_key_provided and not current_plan:
    with st.expander("⚙️ API 키 설정 (선택사항)", expanded=False):
        st.info("💡 샘플 계획이 이미 준비되어 있습니다! API 키 없이도 테스트 가능")
        
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

# 계획 생성
with st.expander("📝 여행 계획", expanded=not bool(current_plan)):
    if current_plan:
        st.success(f"✅ 계획: {current_plan.get('destination', '서울 하루 여행')}")
        st.write(f"활동: {len(current_plan.get('activities', []))}개")
        
        if st.button("초기화", type="secondary"):
            st.session_state.rag.plans = {"plans": [], "current_plan_id": None}
            st.session_state.rag._save_plans()
            st.session_state.movement_path = []
            st.session_state.current_activity_index = 0
            st.session_state.auto_playing = False
            st.session_state.simulator.state["notifications"] = []
            st.rerun()
    else:
        plan_input = st.text_area(
            "새 계획 입력 (API 키 필요)",
            height=80,
            placeholder="예: 서울 하루 여행. 경복궁, 북촌 한식당, 인사동, 명동"
        )
        
        if st.button("생성", use_container_width=True, type="primary"):
            if plan_input and st.session_state.api_key_provided:
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
            elif not st.session_state.api_key_provided:
                st.error("API 키를 먼저 설정하세요")

st.markdown("---")

# 분할 레이아웃
col_left, col_right = st.columns([2, 1])

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
    deck_map = create_map_with_walking_character(
        current_state["location"],
        current_plan,
        st.session_state.movement_path
    )
    st.pydeck_chart(deck_map, use_container_width=True)
    
    # 제어 패널
    st.markdown("### 🎮 제어")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    
    with col_c1:
        if st.button("▶️ 자동 진행", use_container_width=True, type="primary", disabled=st.session_state.auto_playing or not current_plan):
            if current_plan and current_plan.get("activities"):
                st.session_state.auto_playing = True
                st.session_state.current_activity_index = 0
                st.session_state.movement_path = []
                st.session_state.current_step = 0
                st.session_state.waiting_for_notification = False
                st.session_state.notification_to_confirm = None
                
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
            st.session_state.notification_to_confirm = None
            st.rerun()

with col_right:
    st.subheader("📱 안드로이드 화면")
    
    # HTML 핸드폰 UI
    time_info = st.session_state.simulator.get_current_time_info()
    notifications = st.session_state.simulator.state["notifications"]
    
    phone_html = create_phone_html_component(notifications, time_info, current_state['location'])
    
    # HTML 컴포넌트로 표시
    st.components.v1.html(phone_html, height=750, scrolling=False)
    
    # 알림 확인 버튼 (streamlit 네이티브)
    unread = [n for n in notifications if not n.get("read", False)]
    
    if unread and st.session_state.waiting_for_notification:
        st.warning("⚠️ 알림을 확인해주세요!")
        
        for notif in unread:
            actual_idx = notifications.index(notif)
            
            with st.container():
                col_n1, col_n2 = st.columns([3, 1])
                with col_n1:
                    st.write(f"🆕 **{notif.get('title')}**")
                with col_n2:
                    if st.button("✅", key=f"confirm_{actual_idx}", type="primary"):
                        # 알림 읽음 처리
                        st.session_state.simulator.mark_notification_read(actual_idx)
                        st.session_state.waiting_for_notification = False
                        st.rerun()

# 자동 진행 애니메이션 로직
if st.session_state.auto_playing and not st.session_state.waiting_for_notification:
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
        activity = current_plan["activities"][st.session_state.current_activity_index]
        
        # 최종 위치 업데이트
        st.session_state.simulator.update_location(
            activity.get("latitude", 37.5665),
            activity.get("longitude", 126.9780),
            activity.get("location", "목적지")
        )
        
        # 시간 업데이트
        if activity.get("time"):
            time_str = activity.get("time")
            hour, minute = map(int, time_str.split(":"))
            dt = datetime.fromisoformat(st.session_state.simulator.state["datetime"])
            new_dt = dt.replace(hour=hour, minute=minute)
            st.session_state.simulator.update_datetime(new_dt.isoformat())
        
        # 트리거 확인 (한 번만!)
        triggered = st.session_state.rag.check_triggers(
            current_location=st.session_state.simulator.get_state()["location"],
            current_time=datetime.fromisoformat(st.session_state.simulator.state["datetime"]).strftime("%H:%M"),
            current_weather=st.session_state.simulator.get_state()["weather"]
        )
        
        # 알림 생성
        if triggered and not st.session_state.waiting_for_notification:
            for t in triggered:
                act = t["activity"]
                trig = t["trigger"]
                
                notification = {
                    "type": trig.get("type", "general"),
                    "title": act.get("name", "알림"),
                    "message": trig.get("message", "활동 알림"),
                    "activity": act,
                    "trigger": trig,
                    "time": datetime.now().strftime("%H:%M"),
                    "read": False
                }
                st.session_state.simulator.add_notification(notification)
            
            # 알림 확인 대기
            st.session_state.waiting_for_notification = True
            st.rerun()
        
        # 알림이 없으면 다음 활동으로
        if not triggered:
            st.session_state.current_activity_index += 1
            
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
st.caption("🚶 실시간 여행 시뮬레이터 - pydeck + HTML Components")
