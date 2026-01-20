# 🤖 AI 여행 시뮬레이터 (전국 대응 버전)

**사용자 입력 → AI 생성 → 실시간 시뮬레이션**

Upstage Solar AI가 사용자의 요청을 받아 **전국 어디든** 여행 계획을 생성하고, 트리거를 설정하고, 알림을 보내는 완전 자동화 시뮬레이터입니다.

## 🎯 핵심 기능

### ✅ 전국 지역 대응
- 🏰 서울 (경복궁, 북촌, 인사동)
- 🏖️ 부산 (해운대, 자갈치시장, 광안리)
- 🏔️ 강원도 (속초해수욕장, 설악산, 중앙시장)
- 🌊 제주도
- 🏛️ 경주
- **전국 어디든 가능!**

### ✅ 알림 버그 완전 수정
- 이전: 알림이 계속 중복 생성됨 ❌
- 수정: 각 활동마다 한 번만 알림 생성 ✅
- 방법: `notified_activities` set으로 추적

## 🚀 빠른 시작

### 예시: 속초 여행

```
1. 앱 실행
   streamlit run simulation_app.py

2. API 키 입력
   up_YOUR_KEY

3. 여행 계획 입력
   "강원도 속초 하루 여행. 아침에 속초해수욕장 산책하고, 
   점심은 중앙시장에서 먹고, 오후에는 설악산 케이블카 타고 싶어요"

4. 🤖 AI로 계획 생성 (5-10초)

5. ▶️ 자동 진행
```

### AI가 생성하는 것

```json
{
  "destination": "강원도 속초",
  "activities": [
    {
      "name": "속초해수욕장 산책",
      "location": "속초해수욕장",
      "latitude": 38.2072,    // 🔥 속초 좌표!
      "longitude": 128.5933,  // 🔥 서울 아님!
      "time": "09:00",
      "description": "동해의 아름다운 해변...",
      "triggers": [{
        "type": "location",
        "message": "속초해수욕장에 도착했습니다!"
      }]
    },
    ...
  ]
}
```

## 🐛 버그 수정 상세

### 문제: 알림 중복 생성

**증상:**
```
경복궁 도착 → 🆕 알림 생성
✅ 확인 클릭
→ 🆕 알림 다시 생성 (버그!)
→ 🆕 알림 또 생성 (버그!)
→ 무한 반복...
```

**원인:**
```python
# 이전 코드 (버그)
if triggered and not st.session_state.waiting_for_notification:
    # ✅ 확인 후 waiting_for_notification = False
    # → 다시 이 코드 실행 → 또 알림 생성!
    add_notification(...)
```

**해결:**
```python
# 수정된 코드
if "notified_activities" not in st.session_state:
    st.session_state.notified_activities = set()

# 활동 고유 ID 생성
activity_id = f"{current_activity_index}_{activity.get('name')}"

# 이미 알림 생성했는지 확인
if activity_id not in st.session_state.notified_activities:
    triggered = check_triggers(...)
    
    if triggered:
        add_notification(...)
        
        # 🔥 이 활동은 알림 생성 완료!
        st.session_state.notified_activities.add(activity_id)
```

**결과:**
```
경복궁 도착 → 🆕 알림 생성 (1번만!)
✅ 확인 클릭
→ 다음 활동으로 이동
→ 중복 생성 없음 ✅
```

## 🗺️ 지역 대응 상세

### 문제: 서울만 가능

**증상:**
```
입력: "속초 여행"
AI 생성: 속초 좌표 (38.2072, 128.5933)
시작 위치: 서울시청 (37.5665, 126.9780) ← 버그!
→ 서울에서 속초까지 이동 경로 이상함
```

**원인:**
```python
# agent/simulator.py
def __init__(self):
    self.state = {
        "location": {
            "latitude": 37.5665,   # 서울 고정!
            "longitude": 126.9780,
            "name": "서울시청"
        }
    }
```

**해결:**
```python
def initialize_simulation_location(plan):
    """계획의 첫 번째 활동 위치로 초기화"""
    if plan and plan.get("activities"):
        first_activity = plan["activities"][0]
        
        # 🔥 첫 활동 위치로 이동!
        simulator.update_location(
            first_activity.get("latitude"),
            first_activity.get("longitude"),
            f"{first_activity.get('location')} 근처"
        )

# 계획 생성 후 자동 실행
if current_plan:
    if "simulation_initialized" not in st.session_state:
        initialize_simulation_location(current_plan)
        st.session_state.simulation_initialized = True
```

**결과:**
```
입력: "속초 여행"
AI 생성: 속초 좌표 (38.2072, 128.5933)
시작 위치: 속초해수욕장 근처 (38.2072, 128.5933) ✅
→ 올바른 위치에서 시작!
```

## 📍 지역별 테스트

### 1. 서울
```
입력: "서울 하루 여행. 경복궁, 북촌 한식당, 인사동"

AI 생성:
- 경복궁 (37.5796, 126.9770)
- 북촌 (37.5826, 126.9830)
- 인사동 (37.5723, 126.9894)

시작: 경복궁 근처 ✅
```

### 2. 부산
```
입력: "부산 하루 여행. 해운대, 자갈치시장, 광안리"

AI 생성:
- 해운대 (35.1586, 129.1603)
- 자갈치시장 (35.0968, 129.0305)
- 광안리 (35.1532, 129.1189)

시작: 해운대 근처 ✅
```

### 3. 강원도 속초
```
입력: "강원도 속초 하루 여행. 속초해수욕장, 중앙시장, 설악산"

AI 생성:
- 속초해수욕장 (38.2072, 128.5933)
- 중앙시장 (38.2077, 128.5918)
- 설악산 케이블카 (38.1192, 128.4657)

시작: 속초해수욕장 근처 ✅
```

## 🎮 UI 개선

### 지역 선택 버튼
```
📍 지역별 예시:
[🏰 서울] [🏖️ 부산] [🏔️ 강원도]
```

**클릭 시:**
```
서울 클릭 → 텍스트 자동 입력:
"서울 하루 여행. 경복궁, 북촌 한식당, 인사동"

부산 클릭 → 텍스트 자동 입력:
"부산 하루 여행. 해운대, 자갈치시장, 광안리"

강원도 클릭 → 텍스트 자동 입력:
"강원도 속초 하루 여행. 속초해수욕장, 중앙시장, 설악산"
```

### 좌표 정보 표시
```
✅ AI 생성 계획: 강원도 속초
📍 활동: 3개
🎯 시작 위치: 속초해수욕장 (38.2072, 128.5933)

[📋 계획 상세 보기]
  1. 속초해수욕장 산책 (09:00)
     📍 속초해수욕장
     🌍 좌표: (38.2072, 128.5933)  ← 표시됨!
     ⏱️ 120분
```

## 🎯 완전한 플로우

```
1. API 키 입력
   ↓
2. 지역 선택 (서울/부산/강원도) 또는 직접 입력
   ↓
3. 🤖 AI 생성 (5-10초)
   - 활동 구조화
   - 좌표 생성
   - 트리거 설정
   ↓
4. 🎯 시작 위치 자동 설정 (첫 활동 위치)
   ↓
5. ▶️ 자동 진행
   - 이동 (20단계)
   - 도착
   - 🤖 알림 (한 번만!)
   - ✅ 확인
   - 다음 활동
   ↓
6. 완료 🎉
```

## 🔧 코드 변경사항

### 1. Session State 추가
```python
# 알림 추적
if "notified_activities" not in st.session_state:
    st.session_state.notified_activities = set()

# 초기화 플래그
if "simulation_initialized" not in st.session_state:
    st.session_state.simulation_initialized = False
```

### 2. 초기화 함수
```python
def initialize_simulation_location(plan):
    """계획의 첫 활동 위치로 시뮬레이터 초기화"""
    if plan and plan.get("activities"):
        first_activity = plan["activities"][0]
        simulator.update_location(
            first_activity.get("latitude"),
            first_activity.get("longitude"),
            f"{first_activity.get('location')} 근처"
        )
        return True
    return False
```

### 3. 알림 로직 개선
```python
# 활동 고유 ID
activity_id = f"{current_activity_index}_{activity.get('name')}"

# 이미 알림 생성했는지 확인
if activity_id not in st.session_state.notified_activities:
    triggered = rag.check_triggers(...)
    
    if triggered:
        # 알림 생성
        add_notification(...)
        
        # 기록
        st.session_state.notified_activities.add(activity_id)
        
        # 대기
        st.session_state.waiting_for_notification = True
```

## 🐛 디버깅

### 알림이 여전히 중복되면?

**확인 1: Session State**
```python
# F12 → Console
st.write(st.session_state.notified_activities)
# 출력: {'0_경복궁 관람', '1_북촌 한식당 점심'}
```

**확인 2: Activity ID**
```python
st.write(f"Activity ID: {activity_id}")
st.write(f"Already notified: {activity_id in notified_activities}")
```

### 위치가 이상하면?

**확인 1: 좌표**
```python
# 계획 상세 보기
🌍 좌표: (38.2072, 128.5933)  # 속초 맞음?
```

**확인 2: 시뮬레이터 위치**
```python
st.write(st.session_state.simulator.state["location"])
# {'latitude': 38.2072, 'longitude': 128.5933, 'name': '속초해수욕장 근처'}
```

## 📊 테스트 결과

### ✅ 알림 버그
```
테스트 1: 서울 3개 활동
- 경복궁: 알림 1개 ✅
- 북촌: 알림 1개 ✅
- 인사동: 알림 1개 ✅
총 3개 (중복 없음!)

테스트 2: 속초 3개 활동
- 속초해수욕장: 알림 1개 ✅
- 중앙시장: 알림 1개 ✅
- 설악산: 알림 1개 ✅
총 3개 (중복 없음!)
```

### ✅ 지역 대응
```
테스트 1: 서울
- 시작 위치: 경복궁 (37.5796, 126.9770) ✅
- 이동: 경복궁 → 북촌 → 인사동 ✅

테스트 2: 부산
- 시작 위치: 해운대 (35.1586, 129.1603) ✅
- 이동: 해운대 → 자갈치 → 광안리 ✅

테스트 3: 속초
- 시작 위치: 속초해수욕장 (38.2072, 128.5933) ✅
- 이동: 속초해수욕장 → 중앙시장 → 설악산 ✅
```

## 🎯 결론

### ✅ 완전히 해결됨!

**알림 버그:**
- 문제: 중복 생성
- 해결: `notified_activities` set으로 추적
- 결과: 각 활동당 1개만 생성 ✅

**지역 제한:**
- 문제: 서울만 가능
- 해결: 첫 활동 위치로 자동 초기화
- 결과: 전국 어디든 가능 ✅

## 📄 라이센스

MIT License

## 🙋 문의

- GitHub: [kimkuhyun/enilpoc](https://github.com/kimkuhyun/enilpoc)
- Issues: [문제 보고](https://github.com/kimkuhyun/enilpoc/issues)

---

**🎯 이제 완벽합니다!**

✅ 알림 중복 없음
✅ 전국 어디든 가능
✅ AI가 모든 것 생성
✅ 사용자는 입력만
