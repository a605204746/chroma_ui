import React from 'react'
import { createRoot } from 'react-dom/client'
import { initBridge } from '@/bridge'
import App from './App.tsx'
import ErrorBoundary from './components/ErrorBoundary.tsx'
import './i18n'
import 'antd/dist/reset.css'
import './index.css'

async function bootstrap() {
  try {
    await initBridge()
  } catch {
    // 纯浏览器环境（非 pywebview）下 graceful 降级
    console.warn('[bridge] pywebview API not available, running in browser mode')
  }

  createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>,
  )
}

bootstrap()
