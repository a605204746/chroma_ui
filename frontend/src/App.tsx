import { useEffect } from 'react'
import { ConfigProvider, theme } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import enUS from 'antd/locale/en_US'
import { useTranslation } from 'react-i18next'
import AppLayout from './layouts/AppLayout'
import { bridge } from './api/bridge'
import { useAppStore } from './store/appStore'

export default function App() {
  const { setConnections, isDark, syncSystemTheme } = useAppStore()
  const { i18n } = useTranslation()

  useEffect(() => {
    bridge.getConnections().then(setConnections).catch(() => {})
  }, [])

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    mq.addEventListener('change', syncSystemTheme)
    return () => mq.removeEventListener('change', syncSystemTheme)
  }, [syncSystemTheme])

  return (
    <ConfigProvider
      locale={i18n.language === 'en' ? enUS : zhCN}
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: { colorPrimary: '#8b5cf6', borderRadius: 6 },
      }}
    >
      <AppLayout />
    </ConfigProvider>
  )
}
