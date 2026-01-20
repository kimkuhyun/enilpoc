# AI 여행 시뮬레이터

실시간으로 위치, 시간, 날씨를 조작하며 AI 기반 여행 계획을 시뮬레이션하는 MVP 프로젝트입니다.

## 주요 기능

### 1. AI 기반 여행 계획 생성
- 자연어로 여행 계획을 입력하면 LLM이 구조화된 계획 생성
- 장소, 시간, 위도/경도, 트리거 조건을 포함한 상세 계획
- 계획을 RAG 시스템에 저장하여 지능적인 검색 및 수정 가능

### 2. 간편한 시뮬레이션
- **빠른 시나리오**: 계획의 각 활동 위치로 원클릭 이동
- **자동 재생 모드**: 계획에 따라 자동으로 진행
- **수동 제어**: 위치/시간/날씨를 직접 조작
- 서울 주요 관광지 프리셋 지원

### 3. 스마트 알림 시스템
- **위치 기반 트리거**: 목적지 반경 진입 시 자동 알림
- **시간 기반 트리거**: 계획된 시간 도달 시 알림
- **날씨 기반 트리거**: 날씨 변화 시 대안 제안
- 깔끔한 알림 카드로 표시

### 4. 컨텍스트 인식 챗봇
- 알림 클릭 시 즉시 챗봇 연결
- 현재 위치, 시간, 날씨, 계획 정보를 자동으로 포함
- 계획 수정 및 실시간 조언 제공

### 5. 계획 수정 및 업데이트
- 자연어로 계획 수정 요청
- RAG 시스템 자동 업데이트
- 새로운 트리거 조건 자동 생성

## 시스템 아키텍처

```
[Streamlit Web UI]
├── 계획 생성 탭
│   ├── Plan Generator (LLM)
│   └── RAG 저장
│
├── 시뮬레이션 탭
│   ├── 빠른 시나리오 버튼
│   ├── 자동 재생 모드
│   └── 수동 제어 (위치/시간/날씨)
│
├── 모바일 탭
│   ├── 알림 표시
│   └── 챗봇 연결
│
└── 챗봇 탭
    ├── Travel Agent (LLM)
    └── 컨텍스트 자동 주입

[Travel Plan RAG]
├── 계획 저장/검색
├── 트리거 조건 관리
└── 거리 계산 (Haversine)

[Simulator]
├── 위치 시뮬레이션
├── 시간 시뮬레이션
└── 날씨 시뮬레이션
```

## 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd enilpoc
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
`.env` 파일을 생성하고 API 키를 설정하세요:
```env
OPENAI_API_KEY=your_openai_key
# 또는
ANTHROPIC_API_KEY=your_anthropic_key
# 또는
UPSTAGE_API_KEY=your_upstage_key
```

### 5. 앱 실행
```bash
streamlit run simulation_app.py
```

## 사용 방법

### 1단계: 여행 계획 생성
1. "계획 생성" 탭으로 이동
2. 여행 계획을 자유롭게 작성
   - 예: "내일 서울에서 하루 여행 계획해줘. 아침에 경복궁, 점심은 명동, 오후에 남산타워"
3. "계획 생성" 버튼 클릭
4. AI가 구조화된 계획을 생성하고 RAG에 저장

### 2단계: 시뮬레이션 (간편한 방법)

#### 방법 1: 빠른 시나리오 버튼
- "시뮬레이션" 탭에서 활동 버튼을 클릭하면 해당 위치와 시간으로 즉시 이동

#### 방법 2: 자동 재생 모드
- "계획 따라 자동 진행" 버튼으로 계획을 순차적으로 실행

#### 방법 3: 수동 제어
- 위치: 프리셋에서 선택하여 이동
- 시간: +15분, +1시간, +3시간 버튼으로 빠른 진행
- 날씨: 드롭다운에서 선택 후 적용
- "지금 트리거 확인하기" 버튼으로 알림 생성

### 3단계: 알림 확인 및 챗봇 이용
1. "핸드폰" 탭으로 이동
2. 알림 카드 확인
3. "챗봇" 버튼 클릭하여 AI 도우미와 대화
4. 현재 상황에 맞는 조언 및 계획 수정

## 에이전트 플로우

```
[사용자 입력]
    |
[1. 계획 생성]
    ├─ LLM이 자연어를 구조화된 JSON으로 변환
    ├─ 위치 정보 추출 (위도/경도)
    ├─ 트리거 조건 생성
    └─ RAG에 저장
    |
[2. 시뮬레이션]
    ├─ 빠른 시나리오: 원클릭 이동
    ├─ 자동 재생: 계획 순차 실행
    └─ 수동 제어: 위치/시간/날씨 조작
    |
[3. 트리거 감지]
    ├─ 위치 반경 체크 (Haversine 거리)
    ├─ 시간 도달 확인
    └─ 날씨 조건 매칭
    |
[4. 알림 생성]
    ├─ 알림 카드 표시
    └─ 읽지 않은 알림 카운트
    |
[5. 챗봇 연결]
    ├─ 컨텍스트 자동 주입
    ├─ LLM이 상황 기반 응답 생성
    └─ 계획 수정 가능
```

## 주요 컴포넌트

### agent/plan_generator.py
- LLM을 사용하여 자연어를 구조화된 여행 계획으로 변환
- 계획 수정 기능
- OpenAI, Anthropic, Upstage 지원

### agent/plan_rag.py
- 여행 계획 저장 및 검색
- 트리거 조건 확인 (위치/시간/날씨)
- Haversine 거리 계산

### agent/simulator.py
- 위치, 시간, 날씨 시뮬레이션
- 알림 관리
- 서울 주요 관광지 좌표 데이터

### agent/travel_agent.py
- 컨텍스트 인식 대화 에이전트
- 현재 상황 기반 추천
- 대화 기록 관리

### simulation_app.py
- Streamlit 기반 메인 앱
- 4개 탭: 계획 생성, 시뮬레이션, 모바일, 챗봇
- 빠른 시나리오 및 자동 재생 기능

## 데이터 구조

### 여행 계획 JSON
```json
{
  "id": "plan_20250120_143022",
  "destination": "서울",
  "start_date": "2025-01-21",
  "end_date": "2025-01-21",
  "activities": [
    {
      "name": "경복궁 방문",
      "location": "경복궁",
      "latitude": 37.5796,
      "longitude": 126.9770,
      "time": "09:00",
      "duration_minutes": 120,
      "description": "조선시대 궁궐 관람",
      "triggers": [
        {
          "type": "location",
          "latitude": 37.5796,
          "longitude": 126.9770,
          "radius": 0.5,
          "message": "경복궁 근처에 도착했습니다!"
        },
        {
          "type": "time",
          "time": "09:00",
          "message": "경복궁 방문 시간입니다"
        }
      ]
    }
  ]
}
```

## 기술 스택

- **Frontend**: Streamlit
- **LLM**: OpenAI GPT / Anthropic Claude / Upstage Solar
- **Data Storage**: JSON (RAG 시스템)
- **Geospatial**: Haversine distance calculation
- **Python**: 3.8+

## 프로젝트 구조

```
enilpoc/
├── agent/
│   ├── plan_generator.py    # AI 계획 생성기
│   ├── plan_rag.py          # 계획 저장/검색 RAG
│   ├── simulator.py         # 여행 시뮬레이터
│   ├── travel_agent.py      # 대화 에이전트
│   └── tools.py             # 도구 함수
├── utils/
│   ├── config.py            # 설정 관리
│   └── prompts.py           # 프롬프트 템플릿
├── simulation_app.py         # 메인 시뮬레이션 앱
├── travel_plans.json         # 계획 저장소 (자동 생성)
├── requirements.txt
├── .env                      # API 키 (생성 필요)
└── README.md
```

## MVP 특징

이 프로젝트는 **시뮬레이션 중심 MVP**입니다:

- 완전한 에이전트 기능: RAG, 계획 생성, 트리거 시스템 모두 실제 구현
- 간편한 조작: 빠른 시나리오 버튼, 자동 재생 모드
- 알림 시스템: 위치/시간/날씨 기반 자동 알림
- 컨텍스트 챗봇: 현재 상황을 이해하는 AI 도우미

### 실제 앱과의 차이점
- 실제 GPS 대신 프리셋과 수동 조작
- 실제 시간 대신 시뮬레이션 시간 사용
- 실제 API 대신 시뮬레이션 데이터
- 핸드폰 연동 대신 웹 UI로 시뮬레이션

## 향후 개선 사항

1. **실제 API 통합**
   - Google Maps API
   - OpenWeatherMap API
   - 실제 리뷰 데이터

2. **모바일 앱 개발**
   - React Native / Flutter
   - 실제 GPS 연동
   - 푸시 알림

3. **고급 RAG**
   - Vector DB
   - 임베딩 기반 검색
   - 더 정교한 컨텍스트 관리

## 라이센스

MIT License
