import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import zh from './zh'
import en from './en'

const savedLang = localStorage.getItem('chroma-walnut-ui-lang') ?? 'zh'

i18n.use(initReactI18next).init({
  resources: { zh: { translation: zh }, en: { translation: en } },
  lng: savedLang,
  fallbackLng: 'zh',
  interpolation: { escapeValue: false },
})

export default i18n
