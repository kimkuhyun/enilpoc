"""여행 계획 생성 에이전트 - LLM을 사용하여 구조화된 계획 생성."""

from typing import Dict, List
import json
import re
from agent.plan_rag import TravelPlanRAG
from agent.simulator import SEOUL_LANDMARKS
from utils.config import config

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


class PlanGenerator:
    """LLM을 사용하여 구조화된 여행 계획을 생성합니다."""
    
    def __init__(self):
        self.rag = TravelPlanRAG()
        
        # LLM 클라이언트 초기화
        if config.LLM_PROVIDER == "openai" and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.provider = "openai"
        elif config.LLM_PROVIDER == "anthropic" and ANTHROPIC_AVAILABLE:
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self.provider = "anthropic"
        elif config.LLM_PROVIDER == "upstage" and OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=config.UPSTAGE_API_KEY,
                base_url="https://api.upstage.ai/v1/solar"
            )
            self.provider = "upstage"
        else:
            self.client = None
            self.provider = None
    
    def generate_structured_plan(self, user_input: str) -> Dict:
        """사용자 입력을 바탕으로 구조화된 여행 계획을 생성합니다."""
        
        system_prompt = """당신은 여행 계획 전문가입니다. 사용자의 여행 요청을 분석하여 
구조화된 JSON 형태의 여행 계획을 생성합니다.

계획에는 다음이 포함되어야 합니다:
1. 목적지와 날짜
2. 구체적인 활동 목록 (각 활동에는 장소, 시간, 위도/경도, 설명 포함)
3. 각 활동에 대한 트리거 조건 (위치 기반, 시간 기반, 날씨 기반)

사용 가능한 서울 주요 관광지 좌표:
""" + json.dumps(SEOUL_LANDMARKS, ensure_ascii=False, indent=2) + """

응답은 반드시 다음 JSON 형식을 따라야 합니다:
{
  "destination": "목적지",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "activities": [
    {
      "name": "활동명",
      "location": "장소명",
      "latitude": 37.5665,
      "longitude": 126.9780,
      "time": "HH:MM",
      "description": "활동 설명",
      "duration_minutes": 60,
      "triggers": [
        {
          "type": "location",
          "latitude": 37.5665,
          "longitude": 126.9780,
          "radius": 0.5,
          "message": "장소 근처에 도착했습니다"
        },
        {
          "type": "time",
          "time": "09:00",
          "message": "활동 시작 시간입니다"
        }
      ]
    }
  ],
  "preferences": {
    "interests": ["문화", "음식", "자연"],
    "pace": "여유로운"
  }
}

JSON만 반환하고 다른 텍스트는 포함하지 마세요."""

        user_prompt = f"""다음 여행 요청을 구조화된 계획으로 변환해주세요:

{user_input}

JSON 형식으로만 응답해주세요."""

        messages = [{"role": "user", "content": user_prompt}]
        
        if self.provider in ["openai", "upstage"]:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=full_messages,
                temperature=0.3,
                max_tokens=2000
            )
            response_text = response.choices[0].message.content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=config.LLM_MODEL,
                system=system_prompt,
                messages=messages,
                temperature=0.3,
                max_tokens=2000
            )
            response_text = response.content[0].text
        else:
            return {"error": "LLM 클라이언트가 초기화되지 않았습니다"}
        
        # JSON 추출
        try:
            # JSON 코드 블록 제거
            response_text = response_text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            plan_data = json.loads(response_text)
            
            # RAG에 저장
            plan_id = self.rag.create_plan(plan_data)
            plan_data["plan_id"] = plan_id
            
            return plan_data
        
        except json.JSONDecodeError as e:
            return {
                "error": "계획 생성 실패",
                "details": str(e),
                "raw_response": response_text
            }
    
    def modify_plan(self, plan_id: str, modification_request: str) -> Dict:
        """기존 계획을 수정합니다."""
        plan = self.rag.get_current_plan()
        
        if not plan:
            return {"error": "활성 계획이 없습니다"}
        
        system_prompt = f"""현재 여행 계획이 다음과 같습니다:

{json.dumps(plan, ensure_ascii=False, indent=2)}

사용자가 다음과 같이 수정을 요청했습니다: {modification_request}

수정된 전체 계획을 JSON 형식으로 반환해주세요. JSON만 반환하고 다른 텍스트는 포함하지 마세요."""

        messages = [{"role": "user", "content": system_prompt}]
        
        try:
            if self.provider in ["openai", "upstage"]:
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2000
                )
                response_text = response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=2000
                )
                response_text = response.content[0].text
            else:
                return {"error": "LLM 클라이언트가 초기화되지 않았습니다"}
            
            # JSON 추출
            response_text = response_text.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            updated_plan = json.loads(response_text)
            
            # RAG 업데이트
            self.rag.update_plan(plan_id, updated_plan)
            updated_plan["plan_id"] = plan_id
            
            return updated_plan
        
        except Exception as e:
            return {
                "error": "계획 수정 실패",
                "details": str(e)
            }
