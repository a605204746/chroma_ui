import { Card, Radio, Typography, Space, Divider, Tag, theme } from 'antd'
import { SunOutlined, MoonOutlined, LaptopOutlined, DatabaseOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { useAppStore } from '../store/appStore'
import type { ThemeMode } from '../store/appStore'

export default function SystemPage() {
  const { themeMode, setThemeMode } = useAppStore()
  const { token } = theme.useToken()
  const { t } = useTranslation()

  const THEME_OPTIONS: { value: ThemeMode; label: string; icon: React.ReactNode; desc: string }[] = [
    { value: 'light', label: t('theme.light'), icon: <SunOutlined />, desc: t('theme.lightDesc') },
    { value: 'dark', label: t('theme.dark'), icon: <MoonOutlined />, desc: t('theme.darkDesc') },
    { value: 'system', label: t('theme.system'), icon: <LaptopOutlined />, desc: t('theme.systemDesc') },
  ]

  return (
    <div style={{ maxWidth: 680 }}>
      <Typography.Title level={4} style={{ marginBottom: 4 }}>{t('system.title')}</Typography.Title>
      <Typography.Text type="secondary" style={{ fontSize: 13 }}>{t('system.subtitle')}</Typography.Text>
      <Divider style={{ margin: '20px 0' }} />

      <Card styles={{ body: { padding: '20px 24px' } }} style={{ marginBottom: 16 }}>
        <Space size={8} style={{ marginBottom: 16 }}>
          <SunOutlined style={{ color: token.colorPrimary }} />
          <Typography.Text strong>{t('system.appearance')}</Typography.Text>
        </Space>
        <Radio.Group value={themeMode} onChange={e => setThemeMode(e.target.value)} style={{ display: 'flex', gap: 12 }}>
          {THEME_OPTIONS.map(opt => (
            <Radio.Button key={opt.value} value={opt.value} style={{ flex: 1, height: 'auto', padding: '12px 16px', textAlign: 'center', borderRadius: 8 }}>
              <div style={{ fontSize: 18, marginBottom: 4 }}>{opt.icon}</div>
              <div style={{ fontWeight: 600, fontSize: 13 }}>{opt.label}</div>
              <div style={{ fontSize: 11, color: token.colorTextSecondary, marginTop: 2, whiteSpace: 'normal', lineHeight: 1.4 }}>{opt.desc}</div>
            </Radio.Button>
          ))}
        </Radio.Group>
      </Card>

      <Card styles={{ body: { padding: '20px 24px' } }}>
        <Space size={8} style={{ marginBottom: 16 }}>
          <InfoCircleOutlined style={{ color: token.colorPrimary }} />
          <Typography.Text strong>{t('system.about')}</Typography.Text>
        </Space>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Space><DatabaseOutlined style={{ color: '#8b5cf6' }} /><Typography.Text>Chroma UI</Typography.Text></Space>
            <Tag color="purple">v1.0.0</Tag>
          </div>
          <Divider style={{ margin: 0 }} />
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography.Text type="secondary">{t('system.techStack')}</Typography.Text>
            <Space size={4}><Tag>PyWebView</Tag><Tag>React</Tag><Tag>Ant Design</Tag><Tag>ChromaDB</Tag></Space>
          </div>
          <Divider style={{ margin: 0 }} />
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography.Text type="secondary">{t('system.docs')}</Typography.Text>
            <Typography.Link href="https://docs.trychroma.com" target="_blank" style={{ fontSize: 13 }}>docs.trychroma.com</Typography.Link>
          </div>
        </div>
      </Card>
    </div>
  )
}
