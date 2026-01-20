# 🗺️ AI 여행 시뮬레이터

**실시간 이동 애니메이션 + 진짜 안드로이드 핸드폰 UI**

pydeck 2D 지도에서 걷는 캐릭터와 안드로이드 핸드폰 화면을 보며 여행하는 시뮬레이터입니다.

## ✨ 주요 기능

### 1. 실시간 이동 애니메이션 🚶
- 20단계 부드러운 이동 (0.2초 간격)
- 빨간 선으로 이동 경로 표시
- 큰 빨간 원으로 현재 위치 표시

### 2. 진짜 안드로이드 핸드폰 UI 📱
```
┌─────────────────────────┐
│ ⏰ 14:30 📍 경복궁 🔋 100% │ ← 상태바
├─────────────────────────┤
│                         │
│ 🔔 알림 (2 / 5)        │
│                         │
│ ┌─────────────────────┐ │
│ │ 🆕 경복궁 관람      │ │
│ │ 경복궁에 도착했습니다 │ │
│ │ 🕐 14:30           │ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ 점심 식사          │ │
│ │ 북촌 한식당...      │ │
│ │ 🕐 12:00           │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

**진짜 HTML/CSS로 구현:**
- 그라데이션 배경
- 박스 그림자
- 부드러운 border-radius
- 📱 이모지 아이콘

### 3. 샘플 계획 제공 ⭐
**API 키 없이도 바로 테스트 가능!**

```json
{
  "activities": [
    {"name": "경복궁 관람", "time": "09:00"},
    {"name": "북촌 한옥마을 산책", "time": "11:30"},
    {"name": "북촌 한식당 점심", "time": "12:30"},
    {"name": "인사동 쇼핑", "time": "14:00"},
    {"name": "남산타워 전망대", "time": "16:00"},
    {"name": "명동 맛집 저녁", "time": "18:30"}
  ]
}
```

## 🚀 빠른 시작

### 1. 설치
```bash
git clone https://github.com/kimkuhyun/enilpoc.git
cd enilpoc
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. 실행
```bash
streamlit run simulation_app.py
```

### 3. 브라우저 접속
**http://localhost:8501**

### 4. 바로 테스트!
샘플 계획이 이미 준비되어 있습니다:
1. "▶️ 자동 진행" 버튼 클릭
2. 지도에서 빨간 점이 움직이는 것 확인
3. 핸드폰 화면에서 알림 확인
4. ✅ 버튼 클릭 → 다음 활동 시작

## 📋 사용 방법

### 방법 1: 샘플 계획으로 테스트 (권장)
```
1. streamlit run simulation_app.py
2. "▶️ 자동 진행" 클릭
3. 끝! (API 키 불필요)
```

### 방법 2: 새 계획 생성
```
1. API 키 설정 (OpenAI/Anthropic/Upstage)
2. 계획 입력: "서울 하루 여행. 경복궁, 북촌 한식당, 인사동"
3. "생성" 클릭
4. "▶️ 자동 진행" 클릭
```

## 🛠️ 기술 스택

- **Frontend**: Streamlit + HTML/CSS (Components)
- **지도**: pydeck (Deck.gl)
  - ScatterplotLayer: 활동 지점, 현재 위치
  - LineLayer: 이동 경로
- **LLM**: OpenAI / Anthropic / Upstage (선택사항)
- **상태 관리**: Streamlit Session State
- **애니메이션**: time.sleep() + st.rerun()

## 🐛 버그 수정

### ❌ 이전 문제
1. **알림 확인 버튼**: 클릭하면 새 알림이 계속 생성됨
2. **핸드폰 UI**: 제대로 렌더링 안 됨
3. **캐릭터**: 너무 작아서 안 보임

### ✅ 해결 방법
1. **알림 버그**: `waiting_for_notification` 플래그로 중복 생성 방지
   ```python
   # 트리거 확인 (한 번만!)
   if triggered and not st.session_state.waiting_for_notification:
       for t in triggered:
           add_notification(...)
       st.session_state.waiting_for_notification = True
   ```

2. **핸드폰 UI**: `st.components.v1.html()` 사용
   ```python
   phone_html = create_phone_html_component(...)
   st.components.v1.html(phone_html, height=750)
   ```

3. **캐릭터**: ScatterplotLayer radius=200 (크고 명확)

## 📱 안드로이드 UI 구조

```html
<body>
  <div class="phone-frame">      <!-- 검은 테두리 -->
    <div class="status-bar">     <!-- 상태바 (그라데이션) -->
      ⏰ 14:30 | 📍 경복궁 | 🔋 100%
    </div>
    <div class="content">        <!-- 알림 영역 -->
      <div class="notification"> <!-- 알림 카드 -->
        🆕 경복궁 관람
        경복궁에 도착했습니다!
        🕐 14:30
      </div>
    </div>
  </div>
</body>
```

**CSS 특징:**
- `linear-gradient`: 그라데이션 배경
- `box-shadow`: 입체감
- `border-radius`: 부드러운 모서리
- 반응형 디자인

## 🎯 애니메이션 로직

```python
# 1. 경로 생성 (20단계)
path = simulator.simulate_movement(target_lat, target_lon, steps=20)

# 2. 단계별 이동
for step in path:
    simulator.update_location(step)
    time.sleep(0.2)  # 0.2초 대기
    st.rerun()       # 화면 갱신

# 3. 도착 → 알림 확인
if triggered:
    add_notification(...)
    waiting_for_notification = True  # 일시 중지
    
# 4. 사용자가 ✅ 클릭
mark_notification_read(...)
waiting_for_notification = False  # 재개

# 5. 다음 활동으로
current_activity_index += 1
```

## 📊 파일 구조

```
enilpoc/
├── simulation_app.py (521줄)
│   ├── create_phone_html_component()  # 핸드폰 UI HTML 생성
│   ├── create_map_with_walking_character()  # 지도 + 캐릭터
│   └── 자동 진행 로직 (페이지 하단)
│
├── travel_plans.json (샘플 계획)
│
├── agent/
│   ├── plan_generator.py  # LLM 계획 생성
│   ├── plan_rag.py        # 트리거 관리
│   └── simulator.py       # 위치/시간/알림 관리
│
└── requirements.txt
    ├── streamlit>=1.30.0
    ├── pydeck>=0.8.0
    └── openai/anthropic/upstage (선택)
```

## 💡 주요 개선 사항

### Before → After

#### 알림 시스템
```python
# Before (버그)
def check_triggers():
    triggered = rag.check_triggers(...)
    if triggered:
        add_notification(...)  # 계속 생성됨!
    st.rerun()

# After (수정)
def check_triggers():
    if not waiting_for_notification:  # 플래그 확인!
        triggered = rag.check_triggers(...)
        if triggered:
            add_notification(...)
            waiting_for_notification = True  # 중복 방지
```

#### 핸드폰 UI
```python
# Before (작동 안 함)
st.markdown('<div class="phone">...</div>')  # CSS 제한적

# After (작동함!)
html = """
<!DOCTYPE html>
<html>
  <style>
    .phone-frame { ... }  # 완전한 CSS
  </style>
  <body>...</body>
</html>
"""
st.components.v1.html(html, height=750)  # 완벽!
```

## 🎮 버튼 설명

- **▶️ 자동 진행**: 모든 활동 자동 실행
- **⏸️ 정지**: 현재 위치에서 중단
- **🔄 초기화**: 경로/알림 모두 삭제
- **✅ 확인** (핸드폰): 알림 읽음 처리 → 다음 활동

## 🔍 문제 해결

### 앱이 안 켜지면?
```bash
# 1. 가상환경 확인
.\venv\Scripts\Activate.ps1

# 2. 패키지 재설치
pip install -r requirements.txt

# 3. 포트 변경
streamlit run simulation_app.py --server.port 8502
```

### 지도가 안 보이면?
1. 브라우저 콘솔 확인 (F12)
2. `pip show pydeck` 버전 확인
3. 인터넷 연결 확인 (pydeck은 온라인 필요)

### 알림이 안 생기면?
1. `travel_plans.json` 확인
2. 트리거 조건 확인 (time/location)
3. 개발자 도구 콘솔 에러 확인

### 이동이 안 되면?
1. 샘플 계획이 로드되었는지 확인
2. "▶️ 자동 진행" 버튼 클릭했는지 확인
3. `st.session_state.auto_playing` 상태 확인

## 📈 성능

- **20단계 이동**: 약 4초 (20 × 0.2초)
- **메모리**: ~50MB (경로 데이터)
- **CPU**: 낮음 (단순 위치 업데이트)
- **네트워크**: pydeck 타일 로딩만 (가벼움)

## 🔮 향후 계획

1. ✅ ~~알림 버그 수정~~
2. ✅ ~~진짜 핸드폰 UI~~
3. ⏳ 걷는 애니메이션 (GIF)
4. ⏳ 실제 경로 (Google Maps API)
5. ⏳ 사운드 효과

## 📄 라이센스

MIT License

## 🙋 문의

- GitHub: [kimkuhyun/enilpoc](https://github.com/kimkuhyun/enilpoc)
- Issues: [문제 보고](https://github.com/kimkuhyun/enilpoc/issues)

---

## 💻 개발자 노트

### 핵심 기술 결정

#### 1. 왜 pydeck?
- ✅ Streamlit 네이티브 지원
- ✅ Deck.gl의 강력한 레이어 시스템
- ✅ 가볍고 빠름
- ❌ 3D 애니메이션 제한적

#### 2. 왜 HTML Component?
- ✅ 완전한 CSS 제어
- ✅ 그라데이션, 그림자 가능
- ✅ 반응형 디자인
- ❌ Python과 양방향 통신 제한

#### 3. 왜 Session State?
- ✅ 간단한 상태 관리
- ✅ 자동 직렬화
- ❌ 복잡한 객체는 주의

### 디버깅 팁

```python
# 1. Session State 확인
st.write(st.session_state)

# 2. 알림 상태 확인
st.write(st.session_state.simulator.state["notifications"])

# 3. 경로 확인
st.write(st.session_state.movement_path)

# 4. 플래그 확인
st.write(f"auto_playing: {st.session_state.auto_playing}")
st.write(f"waiting: {st.session_state.waiting_for_notification}")
```

---

**🎉 완성! API 키 없이도 바로 테스트하세요!**
