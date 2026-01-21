import React from 'react';
import ReactDOM from 'react-dom/client';
import TravelGuideApp from './TravelGuideApp'; // 메인 컴포넌트 불러오기

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <TravelGuideApp />
  </React.StrictMode>
);