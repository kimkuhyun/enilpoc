# AI 여행 시뮬레이터 - 실시간 이동 애니메이션

pydeck 2D 지도에서 실시간으로 이동하는 모습을 보며 안드로이드 핸드폰에서 알림을 받는 여행 시뮬레이터입니다.

## 🎯 주요 기능

### 1. 실시간 이동 애니메이션 🚶
- **20단계 부드러운 이동**: 목적지까지 20단계로 나누어 이동
- **빨리감기 속도**: 0.2초 간격으로 위치 업데이트
- **경로 표시**: 빨간 선으로 이동 경로 그리기
- **캐릭터 표시**: 큰 빨간 원으로 현재 위치 표시

### 2. 안드로이드 핸드폰 UI 📱
```
┌────────────────────┐
│ ⏰ 14:30 📍 경복궁 🔋│ ← 상태바
├────────────────────┤
│                    │
│ 🔔 알림 (2 / 5)   │
│                    │
│ 🆕 경복궁 관람     │
│ 경복궁에 도착했습니다│
│ 🕐 14:30          │
│ [✅ 확인]         │
│                    │
│ 점심 식사          │
│ 북촌 한식당...     │
│ 🕐 12:00          │
│                    │
└────────────────────┘
```

### 3. 자동 진행 흐름
```
[▶️ 자동 진행] 클릭
    ↓
[1단계] 현재 위치에서 첫 활동 지점까지 20단계 경로 생성
    ↓
[2-21단계] 0.2초마다 한 단계씩 이동 (빨리감기)
    ├─ 지도에 빨간 점 이동
    ├─ 경로 선 그리기
    └─ 말풍선: "경복궁으로 이동 중..."
    ↓
[도착]
    ├─ 시간 업데이트
    ├─ 트리거 확인
    └─ 알림 생성 → ⏸ 일시 중지
    ↓
[사용자가 ✅ 확인 클릭]
    ↓
[다음 활동으로 이동]
    ↓
[반복...]
```

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/kimkuhyun/enilpoc.git
cd enilpoc
```

### 2. 가상환경 활성화 & 패키지 설치
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. 실행
```powershell
streamlit run simulation_app.py
```

### 4. 브라우저 접속
**http://localhost:8501**

## 📝 사용 방법

### 1단계: API 키 설정
- OpenAI, Anthropic, 또는 Upstage 선택
- API 키 입력

### 2단계: 계획 생성
```
입력 예시:
"서울 하루 여행. 오전 경복궁 관람, 점심 북촌 한식당, 
오후 인사동 쇼핑, 저녁 남산타워 전망대, 밤 명동 맛집"
```

**AI가 자동 생성:**
- 각 장소의 위도/경도
- 시간 배정
- 음식점, 관광명소 구분
- 트리거 조건

### 3단계: 자동 진행 시작
1. **"▶️ 자동 진행"** 버튼 클릭
2. 지도에서 빨간 점이 움직이는 것 확인
3. 0.2초마다 한 칸씩 이동 (총 20단계)
4. 도착하면 알림 발생

### 4단계: 알림 확인
1. 오른쪽 안드로이드 화면에 🆕 알림 표시
2. **"✅ 확인"** 버튼 클릭
3. 자동으로 다음 활동 시작

## 🔧 기술 스택

- **Frontend**: Streamlit
- **지도**: pydeck (ScatterplotLayer, LineLayer)
- **LLM**: OpenAI / Anthropic / Upstage
- **상태 관리**: Streamlit Session State
- **애니메이션**: st.rerun() + time.sleep()

## 📦 주요 파일

### simulation_app.py (410줄)
```python
# 핵심 함수
create_pydeck_map()      # 2D 지도 생성
                         # - 활동 지점 (파란 원)
                         # - 이동 경로 (빨간 선)
                         # - 현재 위치 (큰 빨간 원)

# 애니메이션 로직 (페이지 하단)
if auto_playing:
    # 20단계 중 현재 단계로 이동
    step = movement_path[current_step]
    simulator.update_location(step)
    
    # 0.2초 대기
    time.sleep(0.2)
    
    # 다음 단계
    current_step += 1
    st.rerun()
```

### agent/plan_generator.py
- 음식점, 관광명소 포함 계획 생성
- 시간대별 적절한 배치

### agent/simulator.py
- `simulate_movement()`: 20단계 경로 생성
- 알림 관리

## ✨ 주요 개선 사항

### 문제 해결

#### 1. ❌ 깜빡임 문제
**원인**: 매 프레임마다 st.rerun() 호출
**해결**: 단계별로 rerun, time.sleep(0.2)로 속도 조절

#### 2. ❌ 안드로이드 화면 안 보임
**원인**: HTML/CSS가 streamlit에서 제대로 렌더링 안 됨
**해결**: `st.container` + `st.success/info`로 순수 streamlit 컴포넌트 사용

#### 3. ❌ 사람 캐릭터 안 보임
**원인**: radius가 너무 작음 (80 → 200)
**해결**: ScatterplotLayer radius를 200으로 증가

### 애니메이션 로직

```python
# 이전 (문제)
for step in path:
    update_location(step)
    time.sleep(0.15)
    if i % 3 == 0:  # 3프레임마다
        st.rerun()  # 너무 자주 rerun

# 수정 (해결)
if current_step < total_steps:
    step = path[current_step]
    update_location(step)
    current_step += 1
    
    time.sleep(0.2)  # 단계마다
    st.rerun()  # 정확히 필요할 때만
```

## 🎮 버튼 설명

- **▶️ 자동 진행**: 계획의 모든 활동을 순차적으로 자동 실행
- **⏸️ 정지**: 현재 위치에서 이동 중단
- **🔄 초기화**: 모든 상태 초기화 (경로, 알림 등)

## 📱 안드로이드 UI 특징

### 상태바
- **⏰ 시간**: 현재 시뮬레이션 시간
- **📍 위치**: 현재 위치 이름
- **🔋 배터리**: 항상 100% (시뮬레이션)

### 알림 카드
- **🆕 새 알림**: 초록색 배경 + ✅ 확인 버튼
- **읽은 알림**: 파란색 배경 + 시간 표시

## 🐛 문제 해결

### 지도가 안 보이면?
1. 브라우저 콘솔 확인 (F12)
2. pydeck 버전 확인: `pip show pydeck`
3. streamlit 재시작

### 알림이 안 생기면?
1. 계획이 제대로 생성되었는지 확인
2. 트리거 조건이 있는지 확인
3. 시간과 위치가 맞는지 확인

### 이동이 안 되면?
1. "▶️ 자동 진행" 버튼 클릭했는지 확인
2. Session State 확인: `st.session_state.auto_playing`
3. 계획에 활동이 있는지 확인

## 📊 성능

- **20단계 이동**: 약 4초 (20 × 0.2초)
- **지도 업데이트**: 단계마다 1회
- **메모리 사용**: 경로 데이터 저장 (경량)

## 🔮 향후 개선

1. **더 부드러운 애니메이션**: 60 FPS
2. **사람 아이콘**: 실제 걷는 애니메이션
3. **실제 경로**: Google Maps API 연동
4. **사운드**: 알림 소리 추가

## 📄 라이센스

MIT License

## 🙋‍♂️ 문의

- GitHub Issues: [kimkuhyun/enilpoc](https://github.com/kimkuhyun/enilpoc/issues)
