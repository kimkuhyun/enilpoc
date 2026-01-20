"""Streamlit app for AI Travel Planner & Guide."""

import streamlit as st
from agent.travel_agent import TravelAgent
from utils.config import config

# Page configuration
st.set_page_config(
    page_title="Travel Planner AI",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for additional styling
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

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = TravelAgent()

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! I'm your AI travel assistant. I can help you plan your trip, recommend places based on current weather and your preferences, and provide guidance throughout your journey. Where would you like to go?"
    }]

if "api_key_provided" not in st.session_state:
    st.session_state.api_key_provided = config.is_configured()

# Sidebar
with st.sidebar:
    st.title("Travel Planner AI")
    st.markdown("---")
    
    # API Key Configuration
    st.subheader("Configuration")
    
    # LLM Provider selection
    provider = st.selectbox(
        "LLM Provider",
        ["openai", "anthropic"],
        index=0 if config.LLM_PROVIDER == "openai" else 1
    )
    
    # API Key input
    api_key_input = st.text_input(
        f"{provider.upper()} API Key",
        type="password",
        value="" if not config.is_configured() else "configured",
        help="Enter your API key or set it in .env file"
    )
    
    if api_key_input and api_key_input != "configured":
        if provider == "openai":
            config.OPENAI_API_KEY = api_key_input
        else:
            config.ANTHROPIC_API_KEY = api_key_input
        config.LLM_PROVIDER = provider
        
        # Reinitialize agent with new credentials
        st.session_state.agent = TravelAgent()
        st.session_state.api_key_provided = True
    
    st.markdown("---")
    
    # Features
    st.subheader("Features")
    st.markdown("""
    - Context-aware recommendations
    - Weather-based suggestions
    - Review-backed insights
    - Personalized planning
    """)
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("Quick Actions")
    
    if st.button("Clear Conversation"):
        st.session_state.agent.reset_conversation()
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Conversation cleared. How can I help you plan your next adventure?"
        }]
        st.rerun()
    
    if st.button("Show Current Weather"):
        from agent.tools import TravelTools
        weather = TravelTools.get_current_weather("Seoul")
        st.info(
            f"Weather in {weather['location']}: {weather['condition']}, "
            f"{weather['temp']} - {weather['description']}"
        )
    
    st.markdown("---")
    st.caption("AI-powered travel planning MVP")

# Main content
st.title("🗺️ Travel Planner & Guide")

if not st.session_state.api_key_provided:
    st.warning(
        "Please provide your API key in the sidebar or create a .env file "
        "with your credentials to start using the travel planner."
    )
    st.info(
        "You can get an API key from:\n"
        "- OpenAI: https://platform.openai.com/api-keys\n"
        "- Anthropic: https://console.anthropic.com/"
    )
else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your travel plans..."):
        # Add user message to display
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.chat(prompt)
                st.markdown(response)
        
        # Add assistant response to display
        st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.caption(
    "This is an MVP demo. Weather data and reviews are simulated. "
    "In production, this would connect to real APIs and use RAG for review analysis."
)
