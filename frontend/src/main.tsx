import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './i18n/config';

// Google Places API 동적 로드
function loadGooglePlacesApi() {
  const apiKey = import.meta.env.VITE_GOOGLE_PLACES_API_KEY || '';
  if (!apiKey) {
    // eslint-disable-next-line no-console
    console.warn('VITE_GOOGLE_PLACES_API_KEY 환경변수가 설정되지 않음');
    return;
  }

  // 새로운 script 요소 생성
  const script = document.createElement('script');
  script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places&language=en&loading=async`;
  script.async = true;
  script.defer = true;
  document.head.appendChild(script);
}

loadGooglePlacesApi();

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Could not find root element to mount to');
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
