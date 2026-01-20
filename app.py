"""AI 여행 플래너 & 가이드를 위한 Streamlit 앱."""

import streamlit as st
from agent.travel_agent import TravelAgent
from utils.config import config

# 페이지 설정
st.set_page_config(
    page_title="여행 플래너 AI",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 추가 스타일링을 위한 사용자 정의 CSS
st.markdown("""
    <style>
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .main {
        padding: 1rem;
    }
    h1 {
        padding-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "agent" not in st.session_state:
    st.session_state.agent = TravelAgent()

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "안녕하세요! 저는 AI 여행 도우미입니다. 여행 계획을 세우고, 현재 날씨와 선호도에 맞는 장소를 추천하며, 여행 전반에 걸쳐 가이드를 제공해드립니다. 어디로 가고 싶으신가요?"
    }]

if "api_key_provided" not in st.session_state:
    st.session_state.api_key_provided = config.is_configured()

# 사이드바
with st.sidebar:
    st.title("여행 플래너 AI")
    st.markdown("---")
    
    # API 키 설정
    st.subheader("설정")
    
    # LLM 제공자 선택
    provider = st.selectbox(
        "LLM 제공자",
        ["openai", "anthropic", "upstage"],
        index=0 if config.LLM_PROVIDER == "openai" else 1 if config.LLM_PROVIDER == "anthropic" else 2
    )
    
    # API 키 입력
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
        else:  # upstage
            config.UPSTAGE_API_KEY = api_key_input
        config.LLM_PROVIDER = provider
        
        # 새 자격증명으로 에이전트 재초기화
        st.session_state.agent = TravelAgent()
        st.session_state.api_key_provided = True
    
    st.markdown("---")
    
    # 기능
    st.subheader("주요 기능")
    st.markdown("""
    - 상황 인지형 추천
    - 날씨 기반 제안
    - 리뷰 기반 인사이트
    - 개인화된 계획
    """)
    
    st.markdown("---")
    
    # 빠른 작업
    st.subheader("빠른 작업")
    
    if st.button("대화 초기화"):
        st.session_state.agent.reset_conversation()
        st.session_state.messages = [{
            "role": "assistant",
            "content": "대화가 초기화되었습니다. 다음 모험을 계획하는 데 어떻게 도와드릴까요?"
        }]
        st.rerun()
    
    if st.button("현재 날씨 확인"):
        from agent.tools import TravelTools
        weather = TravelTools.get_current_weather("서울")
        st.info(
            f"{weather['location']}의 날씨: {weather['condition']}, "
            f"{weather['temp']} - {weather['description']}"
        )
    
    st.markdown("---")
    st.caption("AI 기반 여행 계획 MVP")

# 메인 콘텐츠
st.title("🗺️ 여행 플래너 & 가이드")

if not st.session_state.api_key_provided:
    st.warning(
        "사이드바에서 API 키를 입력하거나 .env 파일에 "
        "자격증명을 설정하여 여행 플래너를 사용하세요."
    )
    st.info(
        "API 키는 다음에서 발급받을 수 있습니다:\n"
        "- OpenAI: https://platform.openai.com/api-keys\n"
        "- Anthropic: https://console.anthropic.com/\n"
        "- Upstage: https://console.upstage.ai/"
    )
else:
    # 채팅 메시지 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 채팅 입력
    if prompt := st.chat_input("여행 계획에 대해 무엇이든 물어보세요..."):
        # 사용자 메시지를 표시에 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 에이전트 응답 받기
        with st.chat_message("assistant"):
            with st.spinner("생각하는 중..."):
                response = st.session_state.agent.chat(prompt)
                st.markdown(response)
        
        # 어시스턴트 응답을 표시에 추가
        st.session_state.messages.append({"role": "assistant", "content": response})

# 푸터
st.markdown("---")
st.caption(
    "이것은 MVP 데모입니다. 날씨 데이터와 리뷰는 시뮬레이션됩니다. "
    "프로덕션에서는 실제 API에 연결하고 리뷰 분석에 RAG를 사용할 것입니다."
)
