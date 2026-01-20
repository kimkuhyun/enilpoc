# Enilpoc - AI Travel Planner & Guide

An intelligent travel planning assistant powered by LLM and RAG (Retrieval-Augmented Generation) concepts, designed to provide context-aware recommendations and personalized travel guidance.

## Overview

Enilpoc is an MVP travel planner that goes beyond simple information retrieval by:

- **Understanding Context**: Analyzes weather, time, and location to provide situational recommendations
- **Proactive Assistance**: Identifies missing information and suggests what would be helpful
- **Evidence-Based Recommendations**: Supports suggestions with simulated review data and reasoning
- **Natural Conversation**: Maintains context throughout the planning process

## Features

### 1. Travel Planning Assistant
- Natural language trip planning
- Considers purpose, companions, duration, and preferences
- Generates personalized itineraries

### 2. Context-Aware Guide
- Real-time weather integration (simulated in MVP)
- Location-based recommendations
- Time-of-day appropriate suggestions

### 3. Intelligent Recommendations
- Analyzes planned activities against current conditions
- Suggests alternatives when plans aren't suitable
- Explains reasoning behind recommendations

## Tech Stack

- **Frontend**: Streamlit
- **LLM Integration**: OpenAI / Anthropic APIs
- **Language**: Python 3.8+
- **Configuration**: python-dotenv

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/kimkuhyun/enilpoc.git
cd enilpoc
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
OPENAI_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=your_key_here

LLM_PROVIDER=openai  # or anthropic
LLM_MODEL=gpt-4o-mini
```

### 5. Run the application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Project Structure

```
enilpoc/
├── app.py                 # Main Streamlit application
├── agent/
│   ├── __init__.py
│   ├── travel_agent.py    # Core agent logic
│   └── tools.py           # Agent tools (weather, reviews, etc.)
├── utils/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   └── prompts.py         # LLM prompt templates
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── README.md
```

## Usage Examples

### Planning a Trip

```
User: I want to visit Seoul for 3 days
Assistant: Great! To help you plan the perfect trip, could you tell me:
- When are you planning to visit?
- Will you be traveling solo or with companions?
- What are your main interests? (culture, food, nature, etc.)
```

### Getting Recommendations

```
User: What should I do today?
Assistant: [Checks current weather and time]
Given that it's currently rainy and afternoon, I'd recommend:
- Visiting the National Museum (1.2km away) - Reviews mention it's 
  perfect for rainy days and less crowded on weekday afternoons
- Cozy Corner Cafe (500m away) - Great atmosphere for solo travelers
```

## MVP Limitations

This is a 2-week MVP demo with simulated data:

- Weather data is randomly generated (not real API)
- Reviews are from a mock database (not real RAG)
- Location services are simulated
- No actual database or persistence

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes (if using OpenAI) |
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes (if using Anthropic) |
| `LLM_PROVIDER` | LLM provider (`openai` or `anthropic`) | Yes |
| `LLM_MODEL` | Model name | No (default: gpt-4o-mini) |
| `LLM_TEMPERATURE` | Temperature for responses | No (default: 0.7) |
| `MAX_TOKENS` | Maximum tokens per response | No (default: 2000) |

### Theme Colors

The application uses a custom color palette:

- Primary: `#A8DF8E` (soft green)
- Background: `#F0FFDF` (light green)
- Secondary Background: `#FFD8DF` (light pink)
- Accent: `#FFAAB8` (soft pink)

## Contact

Project Link: [https://github.com/kimkuhyun/enilpoc](https://github.com/kimkuhyun/enilpoc)

## Acknowledgments

- Streamlit for the amazing framework
- OpenAI / Anthropic for LLM APIs
- Color palette from [ColorHunt](https://colorhunt.co/palette/a8df8ef0ffdfffd8dfffaab8)
