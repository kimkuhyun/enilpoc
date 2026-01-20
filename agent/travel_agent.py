"""LLM 연동을 포함한 여행 계획 에이전트."""

from typing import List, Dict, Optional
import json

from utils.config import config
from utils.prompts import (
    SYSTEM_PROMPT,
    PLAN_GENERATION_PROMPT,
    SITUATION_ANALYSIS_PROMPT,
    RECOMMENDATION_PROMPT,
    INFO_GATHERING_PROMPT
)
from agent.tools import TravelTools

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class TravelAgent:
    """AI 기반 여행 계획 에이전트."""
    
    def __init__(self):
        self.tools = TravelTools()
        self.conversation_history: List[Dict[str, str]] = []
        
        # 제공자에 따라 LLM 클라이언트 초기화
        if config.LLM_PROVIDER == "openai" and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.provider = "openai"
        elif config.LLM_PROVIDER == "anthropic" and ANTHROPIC_AVAILABLE:
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self.provider = "anthropic"
        elif config.LLM_PROVIDER == "upstage" and OPENAI_AVAILABLE:
            # Upstage는 OpenAI 호환 API 사용
            self.client = OpenAI(
                api_key=config.UPSTAGE_API_KEY,
                base_url="https://api.upstage.ai/v1/solar"
            )
            self.provider = "upstage"
        else:
            self.client = None
            self.provider = None
    
    def _call_llm(self, messages: List[Dict[str, str]], system_prompt: str = SYSTEM_PROMPT) -> str:
        """설정된 제공자에 따라 LLM API를 호출합니다."""
        
        if not self.client:
            return "오류: LLM 클라이언트가 초기화되지 않았습니다. API 키 설정을 확인해주세요."
        
        try:
            if self.provider in ["openai", "upstage"]:
                # 시스템 메시지를 시작 부분에 추가
                full_messages = [{"role": "system", "content": system_prompt}] + messages
                
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=full_messages,
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.MAX_TOKENS
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                # Anthropic은 시스템 파라미터를 별도로 사용
                response = self.client.messages.create(
                    model=config.LLM_MODEL,
                    system=system_prompt,
                    messages=messages,
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.MAX_TOKENS
                )
                return response.content[0].text
        
        except Exception as e:
            return f"LLM 호출 오류: {str(e)}"
    
    def chat(self, user_message: str) -> str:
        """메인 채팅 인터페이스 - 대화와 맥락을 처리합니다."""
        
        # 대화 기록에 사용자 메시지 추가
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # 의도 감지 및 맥락 수집
        context = self._build_context()
        
        # 맥락 정보를 능동적으로 제공해야 하는지 확인
        if self._should_provide_context_info(user_message, context):
            enriched_message = self._enrich_with_context(user_message, context)
            self.conversation_history[-1]["content"] = enriched_message
        
        # LLM 응답 받기
        response = self._call_llm(self.conversation_history)
        
        # 대화 기록에 어시스턴트 응답 추가
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _build_context(self) -> Dict:
        """대화와 현재 상태에서 맥락을 구축합니다."""
        
        # 대화에서 핵심 정보 추출
        context = {
            "destination": None,
            "dates": None,
            "purpose": None,
            "companions": None,
            "preferences": [],
            "current_weather": None,
            "current_time": None
        }
        
        # MVP용 간단한 키워드 추출
        full_text = " ".join([msg["content"] for msg in self.conversation_history if msg["role"] == "user"])
        
        # 위치 언급 확인
        locations = ["서울", "부산", "제주", "도쿄", "파리", "뉴욕"]
        for loc in locations:
            if loc.lower() in full_text.lower():
                context["destination"] = loc
                break
        
        # 활동 선호도 확인
        if "박물관" in full_text.lower() or "문화" in full_text.lower():
            context["preferences"].append("문화")
        if "음식" in full_text.lower() or "맛집" in full_text.lower():
            context["preferences"].append("음식")
        if "자연" in full_text.lower() or "공원" in full_text.lower():
            context["preferences"].append("자연")
        
        return context
    
    def _should_provide_context_info(self, message: str, context: Dict) -> bool:
        """맥락 정보를 능동적으로 추가해야 하는지 판단합니다."""
        
        # 맥락 강화를 트리거하는 키워드
        triggers = [
            "추천", "제안", "어디", "뭐", "무엇",
            "계획", "일정", "방문", "가다"
        ]
        
        return any(trigger in message.lower() for trigger in triggers)
    
    def _enrich_with_context(self, message: str, context: Dict) -> str:
        """메시지에 관련 맥락 정보를 추가합니다."""
        
        enrichments = []
        
        # 목적지를 알 경우 날씨 추가
        if context.get("destination"):
            weather = self.tools.get_current_weather(context["destination"])
            enrichments.append(
                f"\n\n[맥락: {context['destination']}의 현재 날씨: "
                f"{weather['condition']}, {weather['temp']}. {weather['description']}]"
            )
        
        # 시간대 추가
        from datetime import datetime
        hour = datetime.now().hour
        time_of_day = "아침" if hour < 12 else "오후" if hour < 17 else "저녁"
        enrichments.append(f"\n[맥락: 현재 시간은 {time_of_day}입니다]")
        
        return message + "".join(enrichments)
    
    def generate_plan(self, preferences: Dict) -> str:
        """선호도를 바탕으로 여행 계획을 생성합니다."""
        
        context_str = json.dumps(preferences, indent=2, ensure_ascii=False)
        prompt = PLAN_GENERATION_PROMPT.format(context=context_str)
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm(messages)
    
    def analyze_situation(self, activity: str, location: str = "서울") -> str:
        """현재 상황을 분석하고 추천을 제공합니다."""
        
        weather = self.tools.get_current_weather(location)
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        
        # 실행 가능성 분석
        analysis = self.tools.analyze_travel_feasibility(
            activity=activity,
            weather=weather,
            time_of_day=current_time
        )
        
        # 관련 리뷰 가져오기
        reviews = self.tools.get_mock_reviews(activity, weather["condition"])
        
        prompt = SITUATION_ANALYSIS_PROMPT.format(
            activity=activity,
            weather=f"{weather['condition']}, {weather['temp']}",
            time=current_time,
            location=location,
            reviews=reviews
        )
        
        # 프롬프트에 분석 결과 추가
        if not analysis["feasible"]:
            prompt += f"\n\n분석: {analysis['reason']}"
            if analysis['alternatives']:
                alt_str = ", ".join([f"{p['name']} ({p['distance']} 거리)" for p in analysis['alternatives']])
                prompt += f"\n주변 대안: {alt_str}"
        
        messages = [{"role": "user", "content": prompt}]
        return self._call_llm(messages)
    
    def get_recommendations(self, query: str, location: str = "서울") -> str:
        """맥락에 맞는 추천을 제공합니다."""
        
        context = self._build_context()
        weather = self.tools.get_current_weather(location)
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        
        preferences_str = ", ".join(context.get("preferences", ["일반"]))
        
        prompt = RECOMMENDATION_PROMPT.format(
            query=query,
            weather=f"{weather['condition']}, {weather['temp']}",
            location=location,
            time=current_time,
            preferences=preferences_str
        )
        
        messages = [{"role": "user", "content": prompt}]
        return self._call_llm(messages)
    
    def reset_conversation(self):
        """대화 기록을 초기화합니다."""
        self.conversation_history = []
