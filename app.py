import streamlit as st
import json
import os
import re
from dotenv import load_dotenv
from langchain_upstage import ChatUpstage
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from travel_simulator import travel_simulator_component

# 환경 변수 로드
load_dotenv()
st.set_page_config(layout="centered", page_title="VoyageAI")

# --- 스타일 설정 ---
st.markdown("""
<style>
    /* 배경 */
    .stApp { background-color: #FFF5EB; }
    
    /* 텍스트 스타일 */
    h1, h2, h3 { color: #3E2723 !important; font-family: 'Helvetica Neue', sans-serif; letter-spacing: -0.5px; }
    
    /* 카드 스타일 */
    .travel-card { 
        background-color: white; 
        padding: 24px; 
        border-radius: 24px; 
        box-shadow: 0 4px 20px rgba(93, 64, 55, 0.05); 
        margin-bottom: 16px; 
        border: 1px solid #EFEBE9;
    }
    .travel-card h4 { margin-top: 0; color: #5D4037; font-weight: 800; font-size: 1.1rem; }
    .travel-card p { color: #6D4C41; font-size: 0.95rem; line-height: 1.6; margin-bottom: 0; }
    
    /* 채팅 스타일 */
    .stChatMessage { background-color: transparent; }
    .stChatMessage[data-testid="stChatMessageAvatarUser"] { background-color: #8D6E63; }
    .stChatMessage[data-testid="stChatMessageAvatarAssistant"] { background-color: #5D4037; }
    
    /* 버튼 */
    .stButton > button {
        background-color: #3E2723 !important;
        color: #FFCC80 !important;
        border-radius: 16px !important;
        padding: 0.8rem 1.2rem !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.2s;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(62, 39, 35, 0.3); }

    /* 시뮬레이터 컨테이너 중앙 정렬 및 여백 확보 */
    iframe { margin: 0 auto; display: block; height: 850px !important; }
</style>
""", unsafe_allow_html=True)

# --- AI 응답 함수 ---
def get_ai_response(messages):
    api_key = os.getenv("UPSTAGE_API_KEY")
    if not api_key: return "⚠️ .env 파일 설정을 확인해주세요."

    llm = ChatUpstage(api_key=api_key, model="solar-pro2")
    
    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        return f"오류 발생: {e}"

# --- 시스템 프롬프트 (기존 유지) ---
SYSTEM_PROMPT = """
## 행동 지침 (Interaction Protocol)
1. **상담 단계**: 사용자와 대화하며 여행 취향, 인원, 예산 등을 파악하세요. 아직 JSON을 생성하지 마세요.
2. **확정 단계**: 사용자가 계획에 만족하여 "확정", "이대로 해줘"라고 하면, 아래의 **[작업 정의]**와 **[JSON 출력 스키마]**에 따라 완벽한 JSON 데이터를 생성하세요.
3. JSON 생성 시에는 오직 JSON 코드 블록만 출력해야 합니다.

---

## 역할 (Role)
당신은 고도로 지능적인 AI 여행 플래너이자 가이드입니다. 사용자의 여행 목적과 취향을 깊이 있게 이해하고, 실시간 데이터를 활용하여 최적의 여행 경험을 설계하는 전문가 역할을 수행합니다.

## 작업 정의 (Task Definition)
사용자의 입력(Travel Query)과 선택적 정보(Existing Itinerary)를 분석하여 다음 항목을 포함하는 종합적인 여행 데이터를 생성하십시오:
1. **종합 여행 계획**: 사용자의 요구사항을 반영한 최적의 이동 동선.
2. **풍부한 히든 스팟 (필수)**: 주요 이동 경로 주변에 위치한 맛집, 카페, 포토존, 숨겨진 명소 등을 **최소 5개에서 10개 이상** 찾아내십시오. 이는 사용자가 시뮬레이터에서 탐험하며 발견하는 재미를 주기 위함입니다.
3. **거리 제한 (중요)**: `pois`(히든 스팟)는 반드시 `itinerary`의 메인 장소들로부터 **반경 1000m 이내**에 있는 곳들로만 선정하십시오. 너무 먼 곳은 추천하지 마십시오
4. **이유가 포함된 추천**: 각 장소를 추천하는 논리적 근거(리뷰, 평점, 사용자 취향 일치도 등)를 설명에 포함하십시오.
5. **구조화된 데이터**: 지도 및 시뮬레이터 구동을 위한 완벽한 JSON 데이터.


## 정의 및 사양 (Definitions and Specifications)
- **travel_query**: 사용자가 입력한 목적지, 기간, 선호 활동, 예산 등의 자연어 요청입니다.
- **pois (Points of Interest)**: 사용자가 직접 이동하여 찾아낼 "보물찾기" 대상들입니다. 메인 일정(itinerary)에 포함되지 않은 주변의 매력적인 장소여야 합니다.
- **실시간 알림 및 근거**: 각 장소의 `description` 필드에 날씨 고려 사항, 추천 메뉴, 방문 팁 등을 상세히 서술하십시오.

## 역량 활용 (Capabilities Usage)
- **Google Maps Logic**: 실제 존재하는 장소의 **정확한 위도(lat)와 경도(lng)**를 제공해야 합니다. 가상의 좌표를 만들지 마십시오.
- **Trend Search**: 최신 블로그 리뷰와 SNS 핫플레이스 정보를 반영하여 추천의 신뢰도를 높이십시오.

## 최종 응답 요구 사항 (Requirements for the Ending Response)
- **🚨 엄격한 JSON 출력 제약 🚨**: 이 단계의 출력은 반드시 **JSON 포맷**이어야 합니다. 서론, 본론, 결론 같은 텍스트나 마크다운 설명을 절대 포함하지 마십시오.
- **데이터 풍부성**: `pois` 배열에는 반드시 **5개 이상의 다양한 히든 스팟**이 포함되어야 합니다.
- **언어**: 데이터 내의 텍스트(이름, 설명 등)는 반드시 **한국어**로 작성하십시오.

## 실행 및 출력 안내 (Execution and Output Reminder)
심호흡을 하고 모든 지침을 주의 깊게 읽으십시오. 시뮬레이터가 읽을 수 있도록 아래 JSON 스키마를 엄격히 준수하여 출력하십시오.
---
**[JSON 출력 스키마]**
(중괄호는 반드시 JSON 문법에 맞게 작성하며, 위도/경도는 실제 구글 지도 좌표를 사용하세요.)
{{
  "itinerary": [
    {{ "id": 1, "name": "메인 장소명", "lat": 37.xxx, "lng": 127.xxx, "type": "spot", "description": "추천 이유, 팁, 실시간 고려사항을 포함한 상세 설명" }}
  ],
  "pois": [
    {{ "id": 101, "name": "히든 맛집/명소 이름", "lat": 37.xxx, "lng": 127.xxx, "type": "food", "description": "이곳을 발견해야 하는 이유와 특징" }},
    {{ "id": 102, "name": "또 다른 히든 스팟", "lat": 37.xxx, "lng": 127.xxx, "type": "spot", "description": "설명" }}
  ]
}}
"""

# --- Main UI ---
st.title("VoyageAI")
st.caption("Chat with your AI Travel Planner")

if "messages" not in st.session_state:
    st.session_state.messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        AIMessage(content="안녕하세요! VoyageAI입니다. 어디로 여행을 떠나고 싶으신가요? ✈️")
    ]
if "travel_data" not in st.session_state:
    st.session_state.travel_data = None

# 2. 화면 분기 (채팅 vs 시뮬레이터)
if not st.session_state.travel_data:
    # A. 채팅 인터페이스
    for msg in st.session_state.messages:
        if isinstance(msg, (HumanMessage, AIMessage)):
            with st.chat_message(msg.type):
                st.markdown(msg.content)

    if prompt := st.chat_input("메시지를 입력하세요..."):
        st.session_state.messages.append(HumanMessage(content=prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("VoyageAI가 답변을 생성 중입니다..."):
                response_text = get_ai_response(st.session_state.messages)
                
                json_match = re.search(r"```json(.*?)```", response_text, re.DOTALL)
                
                if json_match:
                    try:
                        json_str = json_match.group(1).strip()
                        plan_data = json.loads(json_str)
                        st.session_state.travel_data = plan_data
                        st.success("여행 계획이 확정되었습니다! 시뮬레이터로 이동합니다.")
                        st.rerun()
                    except Exception as e:
                        st.error("데이터 형식 오류가 발생했습니다. 다시 시도해주세요.")
                else:
                    st.markdown(response_text)
                    st.session_state.messages.append(AIMessage(content=response_text))

else:
    # B. 시뮬레이터 & 리포트 인터페이스
    travel_simulator_component(data=st.session_state.travel_data)
    
    st.markdown("### 📋 확정된 여행 코스")
    data = st.session_state.travel_data
    
    if data and 'itinerary' in data:
        for item in data.get('itinerary', []):
            st.markdown(f"""
            <div class="travel-card">
                <h4>📍 {item['name']}</h4>
                <p>{item.get('description', '')}</p>
            </div>
            """, unsafe_allow_html=True)

    if st.button("💬 여행 계획 다시 짜기 (초기화)"):
        st.session_state.travel_data = None
        st.session_state.messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            AIMessage(content="새로운 여행을 계획해 볼까요? 어디로 가고 싶으신가요?")
        ]
        st.rerun()