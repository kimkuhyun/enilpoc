"""여행 에이전트의 설정 관리."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """애플리케이션 설정."""
    
    # LLM 설정
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
    
    # API 키
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    UPSTAGE_API_KEY: Optional[str] = os.getenv("UPSTAGE_API_KEY")
    WEATHER_API_KEY: Optional[str] = os.getenv("WEATHER_API_KEY")
    
    @classmethod
    def get_api_key(cls) -> Optional[str]:
        """제공자에 따라 적절한 API 키를 반환합니다."""
        if cls.LLM_PROVIDER == "openai":
            return cls.OPENAI_API_KEY
        elif cls.LLM_PROVIDER == "anthropic":
            return cls.ANTHROPIC_API_KEY
        elif cls.LLM_PROVIDER == "upstage":
            return cls.UPSTAGE_API_KEY
        return None
    
    @classmethod
    def is_configured(cls) -> bool:
        """최소한의 설정이 존재하는지 확인합니다."""
        return cls.get_api_key() is not None

config = Config()
