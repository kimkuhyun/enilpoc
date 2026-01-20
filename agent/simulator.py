"""여행 시뮬레이터 - 위치, 시간, 날씨 등을 시뮬레이션."""

from typing import Dict, List
from datetime import datetime, timedelta
import json


class TravelSimulator:
    """여행 상황을 시뮬레이션하는 클래스."""
    
    def __init__(self):
        # 초기 시뮬레이션 상태
        self.state = {
            "location": {
                "latitude": 37.5665,  # 서울 시청 기본값
                "longitude": 126.9780,
                "name": "서울시청"
            },
            "datetime": datetime.now().isoformat(),
            "weather": "맑음",
            "temperature": 15,
            "notifications": [],
            "travel_speed": 5,  # km/h (걷기 속도)
        }
    
    def update_location(
        self, 
        latitude: float, 
        longitude: float, 
        location_name: str = "현재 위치"
    ):
        """사용자 위치를 업데이트합니다."""
        self.state["location"] = {
            "latitude": latitude,
            "longitude": longitude,
            "name": location_name
        }
    
    def update_datetime(self, dt_string: str):
        """시뮬레이션 시간을 업데이트합니다."""
        self.state["datetime"] = dt_string
    
    def update_weather(self, weather: str, temperature: int):
        """날씨를 업데이트합니다."""
        self.state["weather"] = weather
        self.state["temperature"] = temperature
    
    def add_notification(self, notification: Dict):
        """알림을 추가합니다."""
        notification["timestamp"] = datetime.now().isoformat()
        notification["read"] = False
        self.state["notifications"].append(notification)
    
    def mark_notification_read(self, notification_id: int):
        """알림을 읽음으로 표시합니다."""
        if 0 <= notification_id < len(self.state["notifications"]):
            self.state["notifications"][notification_id]["read"] = True
    
    def clear_notifications(self):
        """모든 알림을 삭제합니다."""
        self.state["notifications"] = []
    
    def get_unread_notifications(self) -> List[Dict]:
        """읽지 않은 알림을 반환합니다."""
        return [n for n in self.state["notifications"] if not n["read"]]
    
    def get_state(self) -> Dict:
        """현재 시뮬레이션 상태를 반환합니다."""
        return self.state.copy()
    
    def simulate_movement(
        self, 
        target_lat: float, 
        target_lon: float, 
        steps: int = 10
    ) -> List[Dict]:
        """목표 지점까지 단계별로 이동을 시뮬레이션합니다."""
        current_lat = self.state["location"]["latitude"]
        current_lon = self.state["location"]["longitude"]
        
        lat_step = (target_lat - current_lat) / steps
        lon_step = (target_lon - current_lon) / steps
        
        movement_path = []
        
        for i in range(steps + 1):
            new_lat = current_lat + (lat_step * i)
            new_lon = current_lon + (lon_step * i)
            
            movement_path.append({
                "latitude": new_lat,
                "longitude": new_lon,
                "step": i,
                "total_steps": steps
            })
        
        return movement_path
    
    def get_current_time_info(self) -> Dict:
        """현재 시간 정보를 반환합니다."""
        dt = datetime.fromisoformat(self.state["datetime"])
        
        hour = dt.hour
        if 5 <= hour < 12:
            time_of_day = "아침"
        elif 12 <= hour < 17:
            time_of_day = "오후"
        elif 17 <= hour < 21:
            time_of_day = "저녁"
        else:
            time_of_day = "밤"
        
        return {
            "datetime": dt.isoformat(),
            "hour": dt.hour,
            "minute": dt.minute,
            "time_of_day": time_of_day,
            "date": dt.date().isoformat(),
            "day_of_week": dt.strftime("%A")
        }
    
    def advance_time(self, minutes: int = 15):
        """시간을 앞으로 진행합니다."""
        dt = datetime.fromisoformat(self.state["datetime"])
        dt += timedelta(minutes=minutes)
        self.state["datetime"] = dt.isoformat()


# 주요 서울 관광지 좌표 데이터
SEOUL_LANDMARKS = {
    "서울시청": {"lat": 37.5665, "lon": 126.9780},
    "경복궁": {"lat": 37.5796, "lon": 126.9770},
    "남산타워": {"lat": 37.5512, "lon": 126.9882},
    "명동": {"lat": 37.5636, "lon": 126.9834},
    "동대문": {"lat": 37.5708, "lon": 127.0096},
    "홍대입구": {"lat": 37.5568, "lon": 126.9236},
    "강남역": {"lat": 37.4979, "lon": 127.0276},
    "코엑스": {"lat": 37.5115, "lon": 127.0595},
    "롯데월드": {"lat": 37.5111, "lon": 127.0982},
    "북촌한옥마을": {"lat": 37.5826, "lon": 126.9830},
}
