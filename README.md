# 🤖 AI 여행 시뮬레이터 (Upstage Solar)

**실시간 이동 애니메이션 + AI가 생성하는 여행 계획 & 알림**

Upstage Solar AI가 여행 계획을 생성하고, 트리거를 설정하고, 알림을 보내는 완전 자동화 시뮬레이터입니다.

## ✨ AI 기능

### 🤖 Upstage Solar AI가 하는 일

1. **여행 계획 생성**
   - 사용자 입력 → AI가 구조화된 JSON 계획 생성
   - 관광명소, 음식점, 쇼핑 자동 포함
   - 위도/경도, 시간, 소요시간 자동 설정

2. **트리거 생성**
   - 위치 기반 트리거 (도착 시 알림)
   - 시간 기반 트리거 (식사 시간 알림)
   - 날씨 기반 트리거 (우산 준비 등)

3. **알림 메시지 생성**
   - 각 활동에 맞는 AI 생성 메시지
   - 예: "경복궁에 도착했습니다! 입장권은 온라인으로 예매하셨나요?"

## 🚀 빠른 시작

### 1. Upstage API 키 발급
1. [Upstage Console](https://console.upstage.ai) 접속
2. 회원가입/로그인
3. API 키 발급 (`up_...`로 시작)

### 2. 프로젝트 설치
```bash
git clone https://github.com/kimkuhyun/enilpoc.git
cd enilpoc
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 앱 실행
```bash
streamlit run simulation_app.py
```

### 4. API 키 입력
- 브라우저에서 http://localhost:8501 접속
- "Upstage API 키 설정" 섹션에 키 입력
- "설정" 버튼 클릭

### 5. AI로 계획 생성!
```
입력 예시:
"서울 하루 여행. 오전에 경복궁 관람하고, 점심은 북촌 한식당에서 먹고, 
오후에는 인사동에서 쇼핑하고, 저녁은 명동 맛집에서 먹고 싶어요"

↓ AI가 자동 생성 ↓

{
  "destination": "서울 하루 여행",
  "activities": [
    {
      "name": "경복궁 관람",
      "location": "경복궁",
      "latitude": 37.5796,
      "longitude": 126.9770,
      "time": "09:00",
      "duration_minutes": 120,
      "triggers": [
        {
          "type": "location",
          "message": "경복궁에 도착했습니다! 입장권은 온라인으로 예매하셨나요?"
        }
      ]
    },
    ...
  ]
}
```

## 📱 화면 구성

```
┌────────────────────┬──────────────────┐
│ 왼쪽 (지도)        │ 오른쪽 (핸드폰)   │
│                    │                  │
│ 🚶 AI 계획 실행 중 │ ⏰ 14:30         │
│                    │ 📍 경복궁        │
│ [지도]             │ 🔋 100%          │
│ - 파란 원: 활동    │                  │
│ - 빨간 선: 경로    │ 🔔 AI 알림       │
│ - 빨간 큰 원: 현재 │                  │
│                    │ ┌──────────────┐ │
│                    │ │🤖 경복궁 관람 │ │
│                    │ │AI 생성 메시지 │ │
│ [▶️][⏸️][🔄]     │ │🕐 14:30      │ │
│                    │ └──────────────┘ │
└────────────────────┴──────────────────┘
```

## 🔧 기술 스택

- **AI**: Upstage Solar API (solar-pro)
- **Frontend**: Streamlit + HTML/CSS Components
- **지도**: pydeck (Deck.gl)
- **상태 관리**: Streamlit Session State

## 📝 AI가 생성하는 것들

### 1. 여행 계획 (plan_generator.py)
```python
def generate_structured_plan(user_input: str):
    # Upstage Solar API 호출
    response = client.chat.completions.create(
        model="solar-pro",
        messages=[...],
        temperature=0.3
    )
    
    # AI가 JSON 응답 생성
    return {
        "destination": "...",
        "activities": [...],
        "triggers": [...]
    }
```

### 2. 트리거 (AI가 자동 설정)
```json
{
  "type": "location",
  "latitude": 37.5796,
  "longitude": 126.9770,
  "radius": 0.5,
  "message": "경복궁에 도착했습니다!"
}
```

### 3. 알림 메시지 (AI가 생성)
- "경복궁에 도착했습니다! 입장권은 온라인으로 예매하셨나요?"
- "점심시간입니다. 북촌 한식당에서 전통 한식을 즐겨보세요!"
- "인사동 거리에 오신 것을 환영합니다!"

## 🎮 사용 방법

### 1단계: API 키 설정
```
1. streamlit run simulation_app.py
2. API 키 입력 (up_...)
3. "설정" 클릭
```

### 2단계: AI로 계획 생성
```
1. 여행 계획 입력
2. "🤖 AI로 계획 생성" 클릭
3. 5-10초 대기 (AI가 생성 중)
4. 계획 확인
```

### 3단계: 자동 진행
```
1. "▶️ 자동 진행" 클릭
2. 지도에서 이동 확인
3. AI 알림 확인
4. "✅" 클릭 → 다음 활동
```

## 🐛 API 키 문제 해결

### API 키가 안 먹히면?

1. **API 키 형식 확인**
   ```
   올바른 형식: up_...
   잘못된 형식: sk-..., key-...
   ```

2. **API 키 재설정**
   ```bash
   # .env 파일 직접 수정
   notepad .env
   
   # 내용:
   UPSTAGE_API_KEY=up_YOUR_KEY_HERE
   LLM_PROVIDER=upstage
   LLM_MODEL=solar-pro
   ```

3. **앱 재시작**
   ```bash
   # Ctrl+C로 종료 후
   streamlit run simulation_app.py
   ```

### API 호출 테스트
```python
# 가상환경에서
python
>>> from openai import OpenAI
>>> client = OpenAI(
...     api_key="up_YOUR_KEY",
...     base_url="https://api.upstage.ai/v1/solar"
... )
>>> response = client.chat.completions.create(
...     model="solar-pro",
...     messages=[{"role": "user", "content": "Hello"}],
...     max_tokens=50
... )
>>> print(response.choices[0].message.content)
```

## 📊 AI 작동 확인

### 계획 생성이 AI에 의한 것인지 확인

1. **계획 상세 보기**
   - "계획 상세 보기" 확장 메뉴 클릭
   - AI가 생성한 description 확인
   - 트리거 메시지 확인 (AI가 생성)

2. **로그 확인**
   - 개발자 도구 (F12) → Console
   - Upstage API 호출 로그 확인

3. **다른 계획 생성**
   - "초기화" → 새로운 입력
   - AI가 매번 다른 계획 생성 확인

## ⚙️ 설정 파일

### .env
```bash
UPSTAGE_API_KEY=up_YOUR_KEY_HERE
LLM_PROVIDER=upstage
LLM_MODEL=solar-pro
LLM_TEMPERATURE=0.7
MAX_TOKENS=2000
```

### utils/config.py
```python
class Config:
    UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
    LLM_PROVIDER = "upstage"
    LLM_MODEL = "solar-pro"
```

## 🔍 디버깅

### AI가 계획을 안 만들면?

1. **API 키 확인**
   ```python
   # simulation_app.py 상단에 추가
   import os
   print(f"API Key: {os.getenv('UPSTAGE_API_KEY')[:10]}...")
   ```

2. **에러 메시지 확인**
   - "AI 응답 보기" 확장 메뉴
   - raw_response 확인

3. **네트워크 확인**
   - 인터넷 연결 확인
   - 방화벽 설정 확인

### 알림이 AI가 만든 게 맞는지 확인

```python
# 알림 메시지에 "🤖" 이모지 포함
notification = {
    "title": f"🤖 {act.get('name')}",
    "message": trig.get("message"),  # AI가 생성한 메시지
    ...
}
```

## 📈 성능

- **AI 계획 생성**: 5-10초
- **이동 애니메이션**: 4초 (20단계 × 0.2초)
- **메모리**: ~50MB

## 🎯 주요 파일

```
enilpoc/
├── simulation_app.py (534줄)
│   └── Upstage API 전용 UI
│
├── agent/
│   ├── plan_generator.py     # AI 계획 생성
│   ├── plan_rag.py            # 트리거 관리
│   └── simulator.py           # 위치/시간/알림
│
├── utils/
│   └── config.py              # Upstage API 설정
│
└── .env                       # API 키
```

## 🔮 다음 단계

- [ ] AI가 날씨 기반 추천 추가
- [ ] AI가 사용자 피드백 학습
- [ ] 다국어 지원 (AI 번역)
- [ ] 실시간 교통 정보 반영

## 📄 라이센스

MIT License

## 🙋 문의

- GitHub: [kimkuhyun/enilpoc](https://github.com/kimkuhyun/enilpoc)
- Issues: [문제 보고](https://github.com/kimkuhyun/enilpoc/issues)

---

## ✅ Upstage API 작동 확인됨

```
Upstage Solar API: ✓ 작동 중
계획 생성: ✓ AI 자동
알림 생성: ✓ AI 자동
트리거: ✓ AI 자동
```

**🤖 모든 기능이 AI에 의해 자동으로 생성됩니다!**
