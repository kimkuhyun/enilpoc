"""여행 계획 RAG 시스템 - 계획 저장 및 검색."""

import json
from typing import List, Dict, Optional
from datetime import datetime
import os
from pathlib import Path


class TravelPlanRAG:
    """여행 계획을 저장하고 검색하는 RAG 시스템."""
    
    def __init__(self, storage_path: str = "travel_plans.json"):
        self.storage_path = storage_path
        self.plans = self._load_plans()
    
    def _load_plans(self) -> Dict:
        """저장된 계획을 로드합니다."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "plans": [],
            "current_plan_id": None
        }
    
    def _save_plans(self):
        """계획을 파일에 저장합니다."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.plans, f, ensure_ascii=False, indent=2)
    
    def create_plan(self, plan_data: Dict) -> str:
        """새로운 여행 계획을 생성하고 저장합니다."""
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        plan = {
            "id": plan_id,
            "created_at": datetime.now().isoformat(),
            "destination": plan_data.get("destination", ""),
            "start_date": plan_data.get("start_date", ""),
            "end_date": plan_data.get("end_date", ""),
            "activities": plan_data.get("activities", []),
            "triggers": plan_data.get("triggers", []),
            "preferences": plan_data.get("preferences", {}),
            "modified_at": datetime.now().isoformat()
        }
        
        self.plans["plans"].append(plan)
        self.plans["current_plan_id"] = plan_id
        self._save_plans()
        
        return plan_id
    
    def get_current_plan(self) -> Optional[Dict]:
        """현재 활성 계획을 반환합니다."""
        if not self.plans["current_plan_id"]:
            return None
        
        for plan in self.plans["plans"]:
            if plan["id"] == self.plans["current_plan_id"]:
                return plan
        return None
    
    def update_plan(self, plan_id: str, updates: Dict) -> bool:
        """기존 계획을 업데이트합니다."""
        for i, plan in enumerate(self.plans["plans"]):
            if plan["id"] == plan_id:
                plan.update(updates)
                plan["modified_at"] = datetime.now().isoformat()
                self.plans["plans"][i] = plan
                self._save_plans()
                return True
        return False
    
    def add_activity(self, plan_id: str, activity: Dict) -> bool:
        """계획에 새 활동을 추가합니다."""
        for plan in self.plans["plans"]:
            if plan["id"] == plan_id:
                plan["activities"].append(activity)
                plan["modified_at"] = datetime.now().isoformat()
                self._save_plans()
                return True
        return False
    
    def check_triggers(
        self, 
        current_location: Dict[str, float],
        current_time: str,
        current_weather: str
    ) -> List[Dict]:
        """현재 상황에서 트리거된 알림을 확인합니다."""
        triggered = []
        plan = self.get_current_plan()
        
        if not plan:
            return triggered
        
        for activity in plan["activities"]:
            triggers = activity.get("triggers", [])
            
            for trigger in triggers:
                if self._check_trigger_condition(
                    trigger, 
                    current_location, 
                    current_time, 
                    current_weather
                ):
                    triggered.append({
                        "activity": activity,
                        "trigger": trigger,
                        "plan_id": plan["id"]
                    })
        
        return triggered
    
    def _check_trigger_condition(
        self,
        trigger: Dict,
        current_location: Dict[str, float],
        current_time: str,
        current_weather: str
    ) -> bool:
        """트리거 조건을 확인합니다."""
        trigger_type = trigger.get("type")
        
        if trigger_type == "location":
            # 위치 기반 트리거
            target_lat = trigger.get("latitude")
            target_lon = trigger.get("longitude")
            radius = trigger.get("radius", 0.5)  # km
            
            distance = self._calculate_distance(
                current_location["latitude"],
                current_location["longitude"],
                target_lat,
                target_lon
            )
            return distance <= radius
        
        elif trigger_type == "time":
            # 시간 기반 트리거
            target_time = trigger.get("time")
            return current_time >= target_time
        
        elif trigger_type == "weather":
            # 날씨 기반 트리거
            target_weather = trigger.get("condition")
            return current_weather == target_weather
        
        return False
    
    def _calculate_distance(
        self, 
        lat1: float, 
        lon1: float, 
        lat2: float, 
        lon2: float
    ) -> float:
        """Haversine 공식으로 두 지점 간 거리를 계산합니다 (km)."""
        from math import radians, cos, sin, asin, sqrt
        
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # 지구 반지름 (km)
        
        return c * r
    
    def get_all_plans(self) -> List[Dict]:
        """모든 계획을 반환합니다."""
        return self.plans["plans"]
    
    def set_current_plan(self, plan_id: str) -> bool:
        """현재 활성 계획을 설정합니다."""
        for plan in self.plans["plans"]:
            if plan["id"] == plan_id:
                self.plans["current_plan_id"] = plan_id
                self._save_plans()
                return True
        return False
