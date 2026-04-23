import { DatabaseOutlined, PlusOutlined } from '@ant-design/icons'
import { Button, Typography } from 'antd'
import { useTranslation } from 'react-i18next'

interface Props {
  onAddConnection: () => void
}

export default function WelcomePage({ onAddConnection }: Props) {
  const { t } = useTranslation()
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 16 }}>
      <DatabaseOutlined style={{ fontSize: 64, color: '#8b5cf6' }} />
      <Typography.Title level={3} style={{ margin: 0 }}>{t('overview.welcome')}</Typography.Title>
      <Typography.Text type="secondary">{t('overview.subtitle')}</Typography.Text>
      <Button type="primary" icon={<PlusOutlined />} size="large" onClick={onAddConnection}>
        {t('overview.addConn')}
      </Button>
    </div>
  )
}
