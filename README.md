# Enilpoc - AI 여행 플래너 & 가이드

LLM과 RAG(검색 증강 생성) 개념을 활용한 지능형 여행 계획 도우미로, 상황 인지형 추천과 개인화된 여행 가이드를 제공합니다.

## 개요

Enilpoc은 단순한 정보 검색을 넘어서는 MVP 여행 플래너입니다:

- **상황 인지**: 날씨, 시간, 위치를 분석하여 상황에 맞는 추천 제공
- **능동적 지원**: 필요한 정보를 파악하고 제안
- **근거 기반 추천**: 시뮬레이션된 리뷰 데이터와 논리적 근거로 추천 설명
- **자연스러운 대화**: 대화 전체의 맥락 유지

## 주요 기능

### 1. 여행 계획 도우미
- 자연어 기반 여행 일정 작성
- 목적, 동행자, 기간, 선호도 고려
- 개인화된 일정 생성

### 2. 상황 인지형 가이드
- 실시간 날씨 연동 (MVP에서는 시뮬레이션)
- 위치 기반 추천
- 시간대별 적절한 제안

### 3. 지능형 추천
- 현재 상황과 계획한 활동 분석
- 조건이 맞지 않을 때 대안 제시
- 추천 이유 명확하게 설명

## 기술 스택

- **프론트엔드**: Streamlit
- **LLM 연동**: OpenAI / Anthropic / Upstage APIs
- **언어**: Python 3.8+
- **설정**: python-dotenv

## 설치 방법

### 1. 레포지토리 클론

```bash
git clone https://github.com/kimkuhyun/enilpoc.git
cd enilpoc
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. API 키 설정

`.env.example`을 `.env`로 복사하고 API 키를 입력하세요:

```bash
cp .env.example .env
```

`.env` 파일을 열어서 인증 정보를 입력:

```env
OPENAI_API_KEY=your_key_here
# 또는
ANTHROPIC_API_KEY=your_key_here
# 또는
UPSTAGE_API_KEY=your_key_here

LLM_PROVIDER=openai  # openai, anthropic, upstage 중 선택
LLM_MODEL=gpt-4o-mini  # 또는 claude-sonnet-4.5, solar-mini
```

### 5. 애플리케이션 실행

```bash
streamlit run app.py
```

앱이 브라우저에서 `http://localhost:8501`로 열립니다

## 프로젝트 구조

```
enilpoc/
├── app.py                 # 메인 Streamlit 애플리케이션
├── agent/
│   ├── __init__.py
│   ├── travel_agent.py    # AI 에이전트 핵심 로직
│   └── tools.py           # 에이전트 도구 (날씨, 리뷰 등)
├── utils/
│   ├── __init__.py
│   ├── config.py          # 설정 관리
│   └── prompts.py         # LLM 프롬프트 템플릿
├── .streamlit/
│   └── config.toml        # Streamlit 테마 설정
├── .env.example           # 환경 변수 템플릿
├── requirements.txt       # Python 의존성
└── README.md
```

## 사용 예시

### 여행 계획하기

```
사용자: 서울에 3일 동안 여행 가려고 해요
봇: 좋아요! 완벽한 여행을 계획하기 위해 몇 가지 알려주세요:
- 언제 방문하실 계획인가요?
- 혼자 여행하시나요, 아니면 동행자가 있나요?
- 주요 관심사가 무엇인가요? (문화, 음식, 자연 등)
```

### 추천 받기

```
사용자: 오늘 뭐 할까요?
봇: [현재 날씨와 시간 확인]
현재 비가 오고 오후라서 다음을 추천드려요:
- 국립박물관 (1.2km 거리) - 리뷰에 따르면 비 오는 날 
  완벽하고 평일 오후는 덜 붐빕니다
- 아늑한 카페 (500m 거리) - 혼자 여행하기 좋은 분위기
```

## MVP 제한사항

이것은 2주 MVP 데모이며 시뮬레이션 데이터를 사용합니다:

- 날씨 데이터는 랜덤 생성 (실제 API 아님)
- 리뷰는 목 데이터베이스 사용 (실제 RAG 아님)
- 위치 서비스 시뮬레이션
- 데이터베이스 없음 (영구 저장 없음)

## 설정

### 환경 변수

| 변수 | 설명 | 필수 여부 |
|------|------|-----------|
| `OPENAI_API_KEY` | OpenAI API 키 | OpenAI 사용 시 필수 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | Anthropic 사용 시 필수 |
| `UPSTAGE_API_KEY` | Upstage API 키 | Upstage 사용 시 필수 |
| `LLM_PROVIDER` | LLM 제공자 (`openai`, `anthropic`, `upstage`) | 필수 |
| `LLM_MODEL` | 모델 이름 | 선택 (기본값: gpt-4o-mini) |
| `LLM_TEMPERATURE` | 응답 온도 | 선택 (기본값: 0.7) |
| `MAX_TOKENS` | 응답 최대 토큰 | 선택 (기본값: 2000) |

### 테마 색상

애플리케이션은 커스텀 색상 팔레트를 사용합니다:

- 주 색상: `#A8DF8E` (연한 녹색)
- 배경: `#F0FFDF` (밝은 녹색)
- 보조 배경: `#FFD8DF` (연한 분홍)
- 강조: `#FFAAB8` (부드러운 분홍)

## 프로덕션 로드맵

- [ ] 실제 날씨 API 연동 (OpenWeatherMap 등)
- [ ] 리뷰 RAG용 벡터 데이터베이스 (Pinecone, Weaviate)
- [ ] 실제 위치 서비스 (Google Places API)
- [ ] 사용자 인증 및 여행 저장
- [ ] 다국어 지원
- [ ] 모바일 최적화 UI
- [ ] 예약 서비스 연동

## API 키 발급

### OpenAI
https://platform.openai.com/api-keys

### Anthropic
https://console.anthropic.com/

### Upstage
1. https://console.upstage.ai/ 접속
2. 회원가입 후 로그인
3. API Keys 메뉴 선택
4. "Create New Key" 버튼 클릭
5. 생성된 키 복사 및 안전하게 보관

## 문의

프로젝트 링크: [https://github.com/kimkuhyun/enilpoc](https://github.com/kimkuhyun/enilpoc)

## 감사의 말

- Streamlit 프레임워크
- OpenAI / Anthropic / Upstage LLM API
- [ColorHunt](https://colorhunt.co/palette/a8df8ef0ffdfffd8dfffaab8) 색상 팔레트
