"""여행 에이전트를 위한 도구 - MVP용 시뮬레이션."""

import random
from datetime import datetime
from typing import Dict, List

class TravelTools:
    """여행 계획을 위한 시뮬레이션 도구 (MVP 버전)."""
    
    @staticmethod
    def get_current_weather(location: str = "서울") -> Dict[str, str]:
        """날씨 데이터 시뮬레이션 - 프로덕션에서는 실제 API 호출."""
        conditions = [
            {"condition": "맑음", "temp": "15°C", "description": "맑은 하늘, 야외 활동하기 좋음"},
            {"condition": "비", "temp": "12°C", "description": "가벼운 비 예상, 실내 활동 권장"},
            {"condition": "흐림", "temp": "10°C", "description": "구름 낀 날씨, 산책하기 적당"},
            {"condition": "구름조금", "temp": "13°C", "description": "변덕스러운 날씨, 유연한 계획 제안"},
        ]
        
        weather = random.choice(conditions)
        weather["location"] = location
        weather["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return weather
    
    @staticmethod
    def get_mock_reviews(place_name: str, context: str = "") -> str:
        """리뷰 요약 시뮬레이션 - 프로덕션에서는 RAG 사용."""
        
        # MVP용 시뮬레이션 리뷰 데이터베이스
        reviews_db = {
            "실내_카페": [
                "방문객들이 조용한 분위기를 높이 평가, 혼자 여행하기 완벽",
                "비 오는 날 인기, 오후 2시 이후 붐빔",
                "작업이나 독서하기 좋음, 안정적인 와이파이"
            ],
            "야외_공원": [
                "날씨 좋을 때 방문 최고, 봄에 아름다움",
                "주말에 붐빌 수 있음, 일찍 도착하는 것이 좋음",
                "산책로가 잘 관리됨"
            ],
            "박물관": [
                "가족들에게 인기, 인터랙티브 전시",
                "전체 관람에 2-3시간 소요",
                "평일 오전이 덜 붐빔"
            ],
            "맛집": [
                "저녁 식사는 예약 권장",
                "현지 요리로 유명, 정통 경험",
                "피크 시간에는 서비스가 느릴 수 있음"
            ]
        }
        
        # 맥락에 맞는 리뷰 유형 매칭
        if "비" in context.lower() or "실내" in context.lower():
            reviews = reviews_db["실내_카페"] + reviews_db["박물관"]
        elif "야외" in context.lower() or "공원" in context.lower():
            reviews = reviews_db["야외_공원"]
        elif "음식" in context.lower() or "맛집" in context.lower():
            reviews = reviews_db["맛집"]
        else:
            reviews = reviews_db["실내_카페"]
        
        selected = random.sample(reviews, min(2, len(reviews)))
        return "리뷰 하이라이트: " + "; ".join(selected)
    
    @staticmethod
    def get_nearby_places(location: str, category: str = "일반") -> List[Dict[str, str]]:
        """근처 장소 시뮬레이션 - 프로덕션에서는 위치 API 사용."""
        
        places_db = {
            "실내": [
                {"name": "아늑한 코너 카페", "distance": "500m", "type": "카페"},
                {"name": "국립박물관", "distance": "1.2km", "type": "박물관"},
                {"name": "시립 도서관", "distance": "800m", "type": "도서관"},
            ],
            "야외": [
                {"name": "중앙 공원", "distance": "600m", "type": "공원"},
                {"name": "강변 산책로", "distance": "1km", "type": "산책로"},
                {"name": "식물원", "distance": "2km", "type": "정원"},
            ],
            "음식": [
                {"name": "로컬 키친", "distance": "300m", "type": "레스토랑"},
                {"name": "거리 음식 시장", "distance": "700m", "type": "시장"},
                {"name": "전통 찻집", "distance": "900m", "type": "찻집"},
            ]
        }
        
        return places_db.get(category, places_db["실내"])
    
    @staticmethod
    def analyze_travel_feasibility(
        activity: str,
        weather: Dict[str, str],
        time_of_day: str
    ) -> Dict[str, any]:
        """주어진 조건에서 계획된 활동의 실행 가능성을 분석합니다."""
        
        # MVP용 간단한 규칙 기반 분석
        is_outdoor = any(word in activity.lower() for word in ["공원", "산책", "야외", "등산", "해변"])
        is_rainy = "비" in weather["condition"].lower()
        
        feasible = True
        reason = ""
        alternatives = []
        
        if is_outdoor and is_rainy:
            feasible = False
            reason = "야외 활동이 계획되었지만 비가 예상됨"
            alternatives = TravelTools.get_nearby_places(weather.get("location", "현재"), "실내")
        elif not is_outdoor and not is_rainy:
            # 좋은 날씨에 실내 활동 - 야외도 제안 가능
            reason = "날씨가 좋아서 야외 활동도 가능"
            alternatives = TravelTools.get_nearby_places(weather.get("location", "현재"), "야외")
        
        return {
            "feasible": feasible,
            "reason": reason,
            "alternatives": alternatives[:2]  # 상위 2개로 제한
        }
