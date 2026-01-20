"""Tools for the travel agent - simulated for MVP."""

import random
from datetime import datetime
from typing import Dict, List

class TravelTools:
    """Simulated tools for travel planning (MVP version)."""
    
    @staticmethod
    def get_current_weather(location: str = "Seoul") -> Dict[str, str]:
        """Simulate weather data - in production would call real API."""
        conditions = [
            {"condition": "Sunny", "temp": "15C", "description": "Clear skies, good for outdoor activities"},
            {"condition": "Rainy", "temp": "12C", "description": "Light rain expected, indoor activities recommended"},
            {"condition": "Cloudy", "temp": "10C", "description": "Overcast, comfortable for walking"},
            {"condition": "Partly Cloudy", "temp": "13C", "description": "Mixed conditions, flexible planning suggested"},
        ]
        
        weather = random.choice(conditions)
        weather["location"] = location
        weather["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        return weather
    
    @staticmethod
    def get_mock_reviews(place_name: str, context: str = "") -> str:
        """Simulate review summaries - in production would use RAG."""
        
        # Simulated review database for MVP
        reviews_db = {
            "indoor_cafe": [
                "Visitors appreciate the quiet atmosphere, perfect for solo travelers",
                "Popular during rainy days, gets crowded after 2pm",
                "Good for working or reading, stable wifi"
            ],
            "outdoor_park": [
                "Best visited in good weather, beautiful in spring",
                "Can be crowded on weekends, arrive early",
                "Walking paths are well-maintained"
            ],
            "museum": [
                "Popular with families, interactive exhibits",
                "Allow 2-3 hours for full visit",
                "Less crowded on weekday mornings"
            ],
            "restaurant": [
                "Reservations recommended for dinner",
                "Known for local cuisine, authentic experience",
                "Service can be slow during peak hours"
            ]
        }
        
        # Match context to review type
        if "rain" in context.lower() or "indoor" in context.lower():
            reviews = reviews_db["indoor_cafe"] + reviews_db["museum"]
        elif "outdoor" in context.lower() or "park" in context.lower():
            reviews = reviews_db["outdoor_park"]
        elif "food" in context.lower() or "restaurant" in context.lower():
            reviews = reviews_db["restaurant"]
        else:
            reviews = reviews_db["indoor_cafe"]
        
        selected = random.sample(reviews, min(2, len(reviews)))
        return "Review highlights: " + "; ".join(selected)
    
    @staticmethod
    def get_nearby_places(location: str, category: str = "general") -> List[Dict[str, str]]:
        """Simulate nearby places - in production would use location API."""
        
        places_db = {
            "indoor": [
                {"name": "Cozy Corner Cafe", "distance": "500m", "type": "Cafe"},
                {"name": "National Museum", "distance": "1.2km", "type": "Museum"},
                {"name": "City Library", "distance": "800m", "type": "Library"},
            ],
            "outdoor": [
                {"name": "Central Park", "distance": "600m", "type": "Park"},
                {"name": "River Walk", "distance": "1km", "type": "Walking Trail"},
                {"name": "Botanical Garden", "distance": "2km", "type": "Garden"},
            ],
            "food": [
                {"name": "Local Kitchen", "distance": "300m", "type": "Restaurant"},
                {"name": "Street Food Market", "distance": "700m", "type": "Market"},
                {"name": "Traditional Tea House", "distance": "900m", "type": "Tea House"},
            ]
        }
        
        return places_db.get(category, places_db["indoor"])
    
    @staticmethod
    def analyze_travel_feasibility(
        activity: str,
        weather: Dict[str, str],
        time_of_day: str
    ) -> Dict[str, any]:
        """Analyze if planned activity is feasible given conditions."""
        
        # Simple rule-based analysis for MVP
        is_outdoor = any(word in activity.lower() for word in ["park", "walk", "outdoor", "hiking", "beach"])
        is_rainy = "rain" in weather["condition"].lower()
        
        feasible = True
        reason = ""
        alternatives = []
        
        if is_outdoor and is_rainy:
            feasible = False
            reason = "Outdoor activity planned but rain is expected"
            alternatives = TravelTools.get_nearby_places(weather.get("location", "current"), "indoor")
        elif not is_outdoor and not is_rainy:
            # Indoor activity on a nice day - might suggest outdoor
            reason = "Weather is good, outdoor activities are also available"
            alternatives = TravelTools.get_nearby_places(weather.get("location", "current"), "outdoor")
        
        return {
            "feasible": feasible,
            "reason": reason,
            "alternatives": alternatives[:2]  # Limit to top 2
        }
