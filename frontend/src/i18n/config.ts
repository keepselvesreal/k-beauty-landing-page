import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import tl from './locales/tl.json';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    tl: { translation: tl },
  },
  lng: localStorage.getItem('language') || 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
