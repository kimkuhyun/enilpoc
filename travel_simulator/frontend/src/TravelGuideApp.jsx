import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import { Navigation, Utensils, CircleHelp, Footprints, Flag, Gift, Plane, Map as MapIcon, Crosshair, ChevronDown, ChevronUp, Target, ArrowUp, Scan, Sparkles, CheckCircle2 } from "lucide-react";

// --- 거리 계산 헬퍼 (Haversine) ---
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371e3;
  const φ1 = (lat1 * Math.PI) / 180;
  const φ2 = (lat2 * Math.PI) / 180;
  const Δφ = ((lat2 - lat1) * Math.PI) / 180;
  const Δλ = ((lon2 - lon1) * Math.PI) / 180;
  const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

const TravelGuideApp = (props) => {
  const data = props.args?.data;
  const itinerary = useMemo(() => data?.itinerary || [], [data]);
  const pois = useMemo(() => data?.pois || [], [data]);

  // --- 상태 관리 ---
  const [currentStep, setCurrentStep] = useState(0);
  
  const currentTarget = useMemo(() => {
    return itinerary[currentStep] || { lat: 37.5665, lng: 126.9780 };
  }, [itinerary, currentStep]);

  const [origin, setOrigin] = useState(currentTarget);
  const [userPos, setUserPos] = useState({ lat: currentTarget.lat, lng: currentTarget.lng, rotation: 0 });
  const [viewCenter, setViewCenter] = useState({ lat: currentTarget.lat, lng: currentTarget.lng });
  
  const posRef = useRef({ lat: currentTarget.lat, lng: currentTarget.lng });
  const keysPressed = useRef({}); 
  
  const [isRoaming, setIsRoaming] = useState(false);
  const [discoveredPois, setDiscoveredPois] = useState(new Set());
  const [isDragging, setIsDragging] = useState(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const viewStartRef = useRef({ lat: 0, lng: 0 });
  
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  
  // [NEW] Gamification States
  const [showMissionIntro, setShowMissionIntro] = useState(false);
  const [foundAlert, setFoundAlert] = useState(null); // 발견 시 팝업

  const MAP_SCALE = 800000; 

  const getMapOffset = useCallback((lat, lng) => {
    const x = (lng - origin.lng) * MAP_SCALE;
    const y = -(lat - origin.lat) * MAP_SCALE; 
    return { x, y };
  }, [origin, MAP_SCALE]);

  const centerOffset = getMapOffset(viewCenter.lat, viewCenter.lng);

  // 현재 씬의 히든 스팟들 (반경 1.5km)
  const currentScenePois = useMemo(() => {
    return pois.filter(poi => {
        const dist = calculateDistance(currentTarget.lat, currentTarget.lng, poi.lat, poi.lng);
        return dist <= 1500; 
    });
  }, [pois, currentTarget]);

  // 진행도 계산
  const foundCount = currentScenePois.filter(p => discoveredPois.has(p.id)).length;
  const totalCount = currentScenePois.length;

  // --- 초기화 & 미션 인트로 ---
  useEffect(() => {
    if (currentTarget) {
        setOrigin(currentTarget);
        posRef.current = { lat: currentTarget.lat, lng: currentTarget.lng };
        setUserPos({ lat: currentTarget.lat, lng: currentTarget.lng, rotation: 0 });
        setViewCenter({ lat: currentTarget.lat, lng: currentTarget.lng });
        setIsRoaming(false);
        setIsPanelOpen(true);
        
        // [UX] 장소 변경 시 시네마틱 인트로 재생
        setShowMissionIntro(true);
        setTimeout(() => setShowMissionIntro(false), 3000); 
    }
  }, [currentStep, currentTarget]);

  // --- 마우스 드래그 ---
  const handleMouseDown = (e) => {
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    viewStartRef.current = { ...viewCenter };
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    e.preventDefault();
    const deltaX = (dragStartRef.current.x - e.clientX);
    const deltaY = (dragStartRef.current.y - e.clientY);
    const latMove = deltaY / MAP_SCALE;
    const lngMove = deltaX / MAP_SCALE;

    setViewCenter({
      lat: viewStartRef.current.lat - latMove, 
      lng: viewStartRef.current.lng + lngMove
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  // --- 키보드 이벤트 ---
  useEffect(() => {
    const handleKeyDown = (e) => { keysPressed.current[e.key.toLowerCase()] = true; };
    const handleKeyUp = (e) => { keysPressed.current[e.key.toLowerCase()] = false; };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
        window.removeEventListener('keydown', handleKeyDown);
        window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // --- 이동 루프 ---
  useEffect(() => {
    if (!isRoaming) return;
    let animationFrameId;
    const MOVE_SPEED = 0.000005; 

    const loop = () => {
        let dx = 0;
        let dy = 0;
        let moved = false;

        if (keysPressed.current['w'] || keysPressed.current['arrowup']) dy += MOVE_SPEED;
        if (keysPressed.current['s'] || keysPressed.current['arrowdown']) dy -= MOVE_SPEED;
        if (keysPressed.current['a'] || keysPressed.current['arrowleft']) dx -= MOVE_SPEED;
        if (keysPressed.current['d'] || keysPressed.current['arrowright']) dx += MOVE_SPEED;

        if (dx !== 0 && dy !== 0) {
            dx *= 0.707;
            dy *= 0.707;
        }

        if (dx !== 0 || dy !== 0) {
            moved = true;
            posRef.current.lat += dy;
            posRef.current.lng += dx;
            let rotation = Math.atan2(dx, dy) * (180 / Math.PI);
            const newPos = { ...posRef.current, rotation };
            setUserPos(newPos);
            setViewCenter({ lat: newPos.lat, lng: newPos.lng }); 
        }
        animationFrameId = requestAnimationFrame(loop);
    };
    loop();
    return () => cancelAnimationFrame(animationFrameId);
  }, [isRoaming]);

  // --- POI 감지 ---
  useEffect(() => {
    Streamlit.setFrameHeight(850);
    if (itinerary.length === 0) return;

    currentScenePois.forEach(poi => {
      const dist = calculateDistance(userPos.lat, userPos.lng, poi.lat, poi.lng);
      if (dist < 60) { 
        if (!discoveredPois.has(poi.id)) {
            setDiscoveredPois(prev => new Set(prev).add(poi.id));
            // [UX] 발견 시 화면 중앙 알림
            setFoundAlert(poi.name);
            setTimeout(() => setFoundAlert(null), 2500);
        }
      }
    });
  }, [userPos, currentScenePois, discoveredPois, itinerary]);

  const handleNextStep = () => {
    if (currentStep < itinerary.length - 1) {
        setIsTransitioning(true);
        setTimeout(() => {
            setCurrentStep(prev => prev + 1);
            setIsTransitioning(false);
        }, 1500);
    }
  };

  const toggleRoaming = () => {
    setIsRoaming(!isRoaming);
    if (!isRoaming) {
        posRef.current = { lat: userPos.lat, lng: userPos.lng };
        setViewCenter(userPos);
    }
  };

  if (!data || itinerary.length === 0) return <div className="text-center p-10">데이터 로딩 중...</div>;

  return (
    <div className="flex justify-center items-center w-full h-screen bg-[#FFF5EB] overflow-hidden">
        
      {/* MOBILE FRAME */}
      <div className="relative w-[480px] h-[820px] bg-black rounded-[50px] shadow-2xl border-[10px] border-gray-900 overflow-hidden ring-4 ring-gray-200/50 shrink-0">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-36 h-8 bg-black rounded-b-3xl z-50 pointer-events-none"></div>
        
        <div className="relative w-full h-full bg-[#EFEBE9] overflow-hidden">
            
            {/* 1. MAP WORLD CONTAINER */}
            <div 
                className={`absolute inset-0 w-full h-full ${isDragging ? 'cursor-grabbing' : 'cursor-grab'} transition-opacity duration-1000 ${isTransitioning ? 'opacity-0 scale-90' : 'opacity-100 scale-100'}`}
                onMouseDown={handleMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp} onMouseLeave={handleMouseUp}
            >
                <div 
                    className="absolute top-1/2 left-1/2 w-0 h-0 overflow-visible transition-transform duration-75 ease-linear"
                    style={{ transform: `translate(${-centerOffset.x}px, ${-centerOffset.y}px)` }}
                >
                    {/* Grid */}
                    <div className="absolute -inset-[4000px] pointer-events-none opacity-10"
                         style={{ backgroundImage: 'radial-gradient(#5D4037 1px, transparent 1px)', backgroundSize: '30px 30px' }}></div>

                    {/* POIs */}
                    {currentScenePois.map(poi => {
                        const pos = getMapOffset(poi.lat, poi.lng);
                        const isDiscovered = discoveredPois.has(poi.id);
                        return (
                            <div key={poi.id} className="absolute transform -translate-x-1/2 -translate-y-1/2 z-10 transition-all duration-500"
                                 style={{ left: `${pos.x}px`, top: `${pos.y}px` }}>
                                <div className={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg border-[3px] border-white transition-all duration-300
                                    ${isDiscovered ? 'bg-[#FFB74D] scale-100' : 'bg-[#8D6E63] animate-bounce-slow'}`}>
                                    {isDiscovered ? <Utensils size={20} color="white" /> : <CircleHelp size={24} color="white" />}
                                </div>
                                {isDiscovered && (
                                    <div className="absolute top-14 left-1/2 -translate-x-1/2 bg-white/95 px-3 py-1.5 rounded-xl text-xs text-[#5D4037] font-bold shadow-xl border border-[#D7CCC8] whitespace-nowrap z-20 flex flex-col items-center">
                                        <span>{poi.name}</span>
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    {/* Main Target */}
                    {(() => {
                        const pos = getMapOffset(currentTarget.lat, currentTarget.lng);
                        return (
                            <div className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center z-20 pointer-events-none"
                                 style={{ left: `${pos.x}px`, top: `${pos.y}px` }}>
                                <div className="relative p-3 rounded-full bg-[#5D4037] border-4 border-white shadow-2xl">
                                    <Target size={28} color="white" />
                                </div>
                                <span className="mt-3 text-sm px-4 py-1.5 rounded-full font-bold bg-[#5D4037] text-white shadow-lg whitespace-nowrap">
                                    {currentTarget.name}
                                </span>
                            </div>
                        );
                    })()}

                    {/* User Character */}
                    {(() => {
                        const pos = getMapOffset(userPos.lat, userPos.lng);
                        return (
                            <div className="absolute z-30 pointer-events-none transform -translate-x-1/2 -translate-y-1/2" 
                                style={{ left: `${pos.x}px`, top: `${pos.y}px` }}>
                                <div className="relative flex flex-col items-center transition-transform duration-200 ease-out"
                                    style={{ transform: `rotate(${userPos.rotation}deg)` }}>
                                    <div className="w-14 h-14 bg-[#3E2723] rounded-full border-[3px] border-white shadow-2xl flex items-center justify-center text-white relative">
                                        {isRoaming ? <ArrowUp size={24} className="animate-pulse" /> : <Navigation size={24} />}
                                    </div>
                                </div>
                            </div>
                        );
                    })()}
                </div>
            </div>

            {/* 2. HUD - INDICATORS (Rectangular Edge Clamping) */}
            <div className="absolute inset-0 pointer-events-none z-30 overflow-hidden rounded-[40px]">
                {/* Center Crosshair */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[#5D4037]/50">
                    <Crosshair size={24} />
                </div>
                
                {currentScenePois.map(poi => {
                    const pos = getMapOffset(poi.lat, poi.lng);
                    const isDiscovered = discoveredPois.has(poi.id);
                    if (isDiscovered) return null; // 이미 찾은 건 표시 안 함

                    const dx = pos.x - centerOffset.x;
                    const dy = pos.y - centerOffset.y;
                    
                    // 화면 절반 크기 (패딩 적용)
                    const halfW = 220; // 480/2 - padding
                    const halfH = 390; // 820/2 - padding

                    // 화면 내부에 있으면 표시 안 함
                    if (Math.abs(dx) < halfW && Math.abs(dy) < halfH) return null;

                    // [핵심] 직사각형 엣지 클램핑 로직
                    // 벡터 (dx, dy)를 직사각형 경계선까지 연장
                    // 기울기 비율 계산
                    const absDx = Math.abs(dx);
                    const absDy = Math.abs(dy);
                    let scale = 1;

                    if (absDx * halfH > absDy * halfW) {
                        // 세로면(좌/우)에 부딪힘
                        scale = halfW / absDx;
                    } else {
                        // 가로면(상/하)에 부딪힘
                        scale = halfH / absDy;
                    }

                    const indX = 240 + dx * scale; // 240 = 화면 너비/2
                    const indY = 410 + dy * scale; // 410 = 화면 높이/2
                    
                    // 화살표 회전 각도 (대상 방향)
                    const rotation = Math.atan2(dx, -dy) * (180 / Math.PI); // CSS rotate 기준 보정

                    return (
                        <div key={`ind-${poi.id}`} 
                             className="absolute w-8 h-8 flex items-center justify-center transition-all duration-100"
                             style={{ left: `${indX}px`, top: `${indY}px`, transform: 'translate(-50%, -50%)' }}>
                            <div className="bg-[#5D4037] text-white p-2 rounded-full shadow-xl border-2 border-white animate-pulse"
                                 style={{ transform: `rotate(${rotation}deg)` }}>
                                <ArrowUp size={16} fill="currentColor" />
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* 3. GAMIFICATION OVERLAYS */}
            
            {/* (A) 미션 인트로 (Cinematic) */}
            {showMissionIntro && (
                <div className="absolute inset-0 bg-black/60 z-50 flex flex-col items-center justify-center animate-fade-in-out pointer-events-none">
                    <div className="bg-white/10 backdrop-blur-md p-6 rounded-3xl border border-white/20 text-center animate-scale-up">
                        <Scan size={48} className="text-[#FFCC80] mx-auto mb-4 animate-spin-slow" />
                        <h2 className="text-[#FFCC80] text-sm font-bold tracking-[0.3em] mb-1">AREA SCAN COMPLETE</h2>
                        <h1 className="text-white text-3xl font-black mb-2">{currentScenePois.length} POINTS</h1>
                        <p className="text-white/80 text-xs">DETECTED IN THIS AREA</p>
                    </div>
                </div>
            )}

            {/* (B) 발견 알림 (Success Pop) */}
            {foundAlert && (
                <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 pointer-events-none">
                    <div className="flex flex-col items-center animate-bounce-in">
                        <div className="bg-[#FFB74D] text-white p-4 rounded-full shadow-2xl border-4 border-white mb-2">
                            <Sparkles size={32} fill="white" />
                        </div>
                        <h1 className="text-4xl font-black text-white drop-shadow-lg tracking-tighter">FOUND!</h1>
                        <div className="bg-black/50 backdrop-blur px-4 py-1 rounded-full mt-2">
                            <span className="text-[#FFCC80] font-bold text-sm">{foundAlert}</span>
                        </div>
                    </div>
                </div>
            )}

            {/* (C) 상시 HUD (Progress) */}
            <div className="absolute top-12 left-6 z-40 pointer-events-none">
                <div className="bg-black/80 backdrop-blur-md px-4 py-2 rounded-full border border-white/10 flex items-center gap-3 shadow-lg">
                    <CheckCircle2 size={18} className={foundCount === totalCount ? "text-[#FFCC80]" : "text-white/50"} />
                    <div className="flex flex-col">
                        <span className="text-[8px] text-white/60 font-bold uppercase tracking-wider">Scanned Points</span>
                        <div className="flex items-baseline gap-1">
                            <span className="text-white font-black text-lg">{foundCount}</span>
                            <span className="text-white/40 text-xs font-bold">/ {totalCount}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 4. BOTTOM SHEET (Controller) */}
            <div className={`absolute bottom-0 left-0 w-full z-50 transition-transform duration-500 ease-in-out ${isPanelOpen ? 'translate-y-0' : 'translate-y-[65%]'}`}>
                <div className="absolute -top-10 left-0 w-full h-10 bg-gradient-to-t from-black/10 to-transparent pointer-events-none"></div>
                <div className="bg-white/95 backdrop-blur-xl rounded-t-[36px] shadow-[0_-10px_40px_rgba(0,0,0,0.1)] border-t border-white/50 pb-8">
                    <div className="w-full flex justify-center pt-3 pb-1 cursor-pointer active:opacity-70" onClick={() => setIsPanelOpen(!isPanelOpen)}>
                        <div className="w-12 h-1.5 bg-[#D7CCC8] rounded-full mb-1"></div>
                    </div>
                    <div className="px-6 pb-4">
                        <div className="flex justify-between items-center mb-3">
                            <div onClick={() => setIsPanelOpen(true)}>
                                <span className="text-[10px] font-bold bg-[#FFF5EB] text-[#8D6E63] px-2 py-1 rounded-md mb-1 inline-block">Current Location</span>
                                <h2 className="text-2xl font-extrabold text-[#3E2723]">{currentTarget.name}</h2>
                            </div>
                            <button onClick={() => setIsPanelOpen(!isPanelOpen)} className="text-[#A1887F] p-1">
                                {isPanelOpen ? <ChevronDown size={20} /> : <ChevronUp size={20} />}
                            </button>
                        </div>
                        <p className="text-sm text-[#6D4C41] leading-relaxed line-clamp-3 mb-6" onClick={() => setIsPanelOpen(true)}>{currentTarget.description}</p>
                        <div className="flex gap-3">
                            <button onClick={toggleRoaming} className={`flex-1 flex items-center justify-center gap-2 py-3.5 rounded-2xl font-bold text-sm transition-all border
                                ${isRoaming ? 'bg-[#5D4037] text-white border-transparent' : 'bg-[#EFEBE9] text-[#5D4037] border-transparent'}`}>
                                {isRoaming ? <><Crosshair size={18} /> 탐험 종료</> : <><Footprints size={18} /> 탐험하기</>}
                            </button>
                            <button onClick={handleNextStep} disabled={currentStep >= itinerary.length - 1} className="flex-[2] flex items-center justify-between bg-[#3E2723] text-white px-5 py-3.5 rounded-2xl shadow-lg active:scale-95 transition-transform disabled:opacity-50 disabled:active:scale-100">
                                <div className="flex flex-col items-start">
                                    <span className="text-[9px] text-[#A1887F] font-bold uppercase">NEXT</span>
                                    <span className="text-sm font-bold truncate max-w-[120px]">{currentStep >= itinerary.length - 1 ? "End" : itinerary[currentStep + 1]?.name}</span>
                                </div>
                                <div className="bg-[#5D4037] p-2 rounded-lg"><Plane size={18} className="text-[#FFCC80]" /></div>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default withStreamlitConnection(TravelGuideApp);