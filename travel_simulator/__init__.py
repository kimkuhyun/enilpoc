import os
import streamlit.components.v1 as components

# 개발 모드 여부 (npm run start로 실행 중일 때 True)
_RELEASE = True 

if not _RELEASE:
    _component_func = components.declare_component(
        "travel_simulator",
        url="http://localhost:3000",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component(
        "travel_simulator",
        path=build_dir
    )

def travel_simulator_component(data, key=None):
    """
    data: {"itinerary": [], "pois": []} 형태의 JSON
    """
    return _component_func(data=data, key=key, default=None)