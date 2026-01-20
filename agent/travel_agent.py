"""Travel planning agent with LLM integration."""

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
    """AI-powered travel planning agent."""
    
    def __init__(self):
        self.tools = TravelTools()
        self.conversation_history: List[Dict[str, str]] = []
        
        # Initialize LLM client based on provider
        if config.LLM_PROVIDER == "openai" and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            self.provider = "openai"
        elif config.LLM_PROVIDER == "anthropic" and ANTHROPIC_AVAILABLE:
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self.provider = "anthropic"
        else:
            self.client = None
            self.provider = None
    
    def _call_llm(self, messages: List[Dict[str, str]], system_prompt: str = SYSTEM_PROMPT) -> str:
        """Call LLM API based on configured provider."""
        
        if not self.client:
            return "Error: LLM client not initialized. Please check your API key configuration."
        
        try:
            if self.provider == "openai":
                # Add system message to the beginning
                full_messages = [{"role": "system", "content": system_prompt}] + messages
                
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=full_messages,
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.MAX_TOKENS
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                # Anthropic uses system parameter separately
                response = self.client.messages.create(
                    model=config.LLM_MODEL,
                    system=system_prompt,
                    messages=messages,
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.MAX_TOKENS
                )
                return response.content[0].text
        
        except Exception as e:
            return f"Error calling LLM: {str(e)}"
    
    def chat(self, user_message: str) -> str:
        """Main chat interface - handles conversation and context."""
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Detect intent and gather context
        context = self._build_context()
        
        # Check if we should proactively provide information
        if self._should_provide_context_info(user_message, context):
            enriched_message = self._enrich_with_context(user_message, context)
            self.conversation_history[-1]["content"] = enriched_message
        
        # Get LLM response
        response = self._call_llm(self.conversation_history)
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _build_context(self) -> Dict:
        """Build context from conversation and current state."""
        
        # Extract key information from conversation
        context = {
            "destination": None,
            "dates": None,
            "purpose": None,
            "companions": None,
            "preferences": [],
            "current_weather": None,
            "current_time": None
        }
        
        # Simple keyword extraction for MVP
        full_text = " ".join([msg["content"] for msg in self.conversation_history if msg["role"] == "user"])
        
        # Check for location mentions
        locations = ["Seoul", "Busan", "Jeju", "Tokyo", "Paris", "New York"]
        for loc in locations:
            if loc.lower() in full_text.lower():
                context["destination"] = loc
                break
        
        # Check for activity preferences
        if "museum" in full_text.lower() or "culture" in full_text.lower():
            context["preferences"].append("cultural")
        if "food" in full_text.lower() or "restaurant" in full_text.lower():
            context["preferences"].append("food")
        if "nature" in full_text.lower() or "park" in full_text.lower():
            context["preferences"].append("nature")
        
        return context
    
    def _should_provide_context_info(self, message: str, context: Dict) -> bool:
        """Determine if we should proactively add contextual information."""
        
        # Keywords that trigger context enhancement
        triggers = [
            "recommend", "suggest", "where", "what to do",
            "plan", "itinerary", "visit", "go to"
        ]
        
        return any(trigger in message.lower() for trigger in triggers)
    
    def _enrich_with_context(self, message: str, context: Dict) -> str:
        """Add relevant contextual information to the message."""
        
        enrichments = []
        
        # Add weather if destination is known
        if context.get("destination"):
            weather = self.tools.get_current_weather(context["destination"])
            enrichments.append(
                f"\n\n[Context: Current weather in {context['destination']}: "
                f"{weather['condition']}, {weather['temp']}. {weather['description']}]"
            )
        
        # Add time of day
        from datetime import datetime
        hour = datetime.now().hour
        time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
        enrichments.append(f"\n[Context: Current time is {time_of_day}]")
        
        return message + "".join(enrichments)
    
    def generate_plan(self, preferences: Dict) -> str:
        """Generate a travel plan based on preferences."""
        
        context_str = json.dumps(preferences, indent=2)
        prompt = PLAN_GENERATION_PROMPT.format(context=context_str)
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        return self._call_llm(messages)
    
    def analyze_situation(self, activity: str, location: str = "Seoul") -> str:
        """Analyze current situation and provide recommendations."""
        
        weather = self.tools.get_current_weather(location)
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        
        # Get feasibility analysis
        analysis = self.tools.analyze_travel_feasibility(
            activity=activity,
            weather=weather,
            time_of_day=current_time
        )
        
        # Get relevant reviews
        reviews = self.tools.get_mock_reviews(activity, weather["condition"])
        
        prompt = SITUATION_ANALYSIS_PROMPT.format(
            activity=activity,
            weather=f"{weather['condition']}, {weather['temp']}",
            time=current_time,
            location=location,
            reviews=reviews
        )
        
        # Add analysis results to prompt
        if not analysis["feasible"]:
            prompt += f"\n\nAnalysis: {analysis['reason']}"
            if analysis['alternatives']:
                alt_str = ", ".join([f"{p['name']} ({p['distance']} away)" for p in analysis['alternatives']])
                prompt += f"\nNearby alternatives: {alt_str}"
        
        messages = [{"role": "user", "content": prompt}]
        return self._call_llm(messages)
    
    def get_recommendations(self, query: str, location: str = "Seoul") -> str:
        """Get contextual recommendations."""
        
        context = self._build_context()
        weather = self.tools.get_current_weather(location)
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M")
        
        preferences_str = ", ".join(context.get("preferences", ["general"]))
        
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
        """Reset conversation history."""
        self.conversation_history = []
