import { useEffect, useState } from 'react'
import { Card, Col, Row, Typography, Button, Table, Tag, Space, Empty, Badge, theme } from 'antd'
import {
  DatabaseOutlined, FileTextOutlined, PlusOutlined,
  TableOutlined, FolderOutlined, GlobalOutlined, DesktopOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'
import type { Collection } from '../types'
import type { ColumnsType } from 'antd/es/table'
import WalnutLogo from '../components/WalnutLogo'

interface Props { onAddConnection: () => void }

interface StatCardProps { title: string; value: string | number; icon: React.ReactNode; color: string }

function StatCard({ title, value, icon, color }: StatCardProps) {
  const { token } = theme.useToken()
  return (
    <Card style={{ height: '100%' }} styles={{ body: { padding: '20px 24px' } }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{
          width: 48, height: 48, borderRadius: 12, background: color + '18',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <span style={{ fontSize: 22, color }}>{icon}</span>
        </div>
        <div>
          <div style={{ fontSize: 12, color: token.colorTextSecondary, marginBottom: 4 }}>{title}</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: token.colorText, lineHeight: 1 }}>{value}</div>
        </div>
      </div>
    </Card>
  )
}

export default function OverviewPage({ onAddConnection }: Props) {
  const { activeConnId, connections, collections, setCollections, navigateToCollection, setCurrentNav } = useAppStore()
  const { token } = theme.useToken()
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const activeConn = connections.find(c => c.id === activeConnId)

  useEffect(() => {
    if (!activeConnId) return
    setLoading(true)
    bridge.listCollections(activeConnId)
      .then(cols => setCollections(Array.isArray(cols) ? cols : []))
      .finally(() => setLoading(false))
  }, [activeConnId])

  const totalDocs = collections.reduce((sum, c) => sum + c.count, 0)

  const connTypeIcon = activeConn?.conn_type === 'persistent'
    ? <FolderOutlined /> : activeConn?.is_local ? <DesktopOutlined /> : <GlobalOutlined />

  const connTypeLabel = activeConn?.conn_type === 'persistent' ? t('conn.localDir') : t('conn.http')

  const connTypeColor = activeConn?.conn_type === 'persistent' ? 'orange' : 'blue'

  const connAddress = activeConn?.conn_type === 'persistent'
    ? activeConn.path : `${activeConn?.host}:${activeConn?.port}`

  const columns: ColumnsType<Collection> = [
    {
      title: t('collections.colName'), dataIndex: 'name', key: 'name',
      render: (name: string) => (
        <Typography.Link onClick={() => navigateToCollection(name)} style={{ fontWeight: 500 }}>{name}</Typography.Link>
      ),
    },
    {
      title: t('collections.docCount'), dataIndex: 'count', key: 'count', width: 120,
      render: (count: number) => <Tag color="blue" style={{ fontFamily: 'monospace' }}>{count.toLocaleString()}</Tag>,
    },
    {
      title: t('collections.action'), key: 'action', width: 80,
      render: (_, record) => (
        <Button type="link" size="small" onClick={() => navigateToCollection(record.name)}>{t('overview.view')}</Button>
      ),
    },
  ]

  if (!activeConnId) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '60vh', gap: 16 }}>
        <WalnutLogo size={88} />
        <Typography.Title level={3} style={{ margin: 0 }}>{t('overview.welcome')}</Typography.Title>
        <Typography.Text type="secondary">{t('overview.subtitle')}</Typography.Text>
        <Button type="primary" size="large" icon={<PlusOutlined />} onClick={onAddConnection}>
          {t('overview.addConn')}
        </Button>
      </div>
    )
  }

  return (
    <div>
      <Card style={{ marginBottom: 20, borderLeft: `4px solid ${token.colorPrimary}` }} styles={{ body: { padding: '16px 20px' } }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Space size={16} align="center">
            <div style={{
              width: 44, height: 44, borderRadius: 10, background: `${token.colorPrimary}18`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <DatabaseOutlined style={{ fontSize: 20, color: token.colorPrimary }} />
            </div>
            <div>
              <Space size={8} align="center">
                <Typography.Text strong style={{ fontSize: 18 }}>{activeConn?.name}</Typography.Text>
                <Badge status="success" />
                <Typography.Text type="secondary" style={{ fontSize: 13 }}>{t('overview.connected')}</Typography.Text>
              </Space>
              <div style={{ marginTop: 2 }}>
                <Space size={6}>
                  <Tag icon={connTypeIcon} color={connTypeColor} style={{ margin: 0 }}>{connTypeLabel}</Tag>
                  <Typography.Text type="secondary" style={{ fontSize: 12, fontFamily: 'monospace' }} copyable={{ tooltips: false }}>
                    {connAddress}
                  </Typography.Text>
                </Space>
              </div>
            </div>
          </Space>
        </div>
      </Card>

      <Row gutter={[16, 16]} style={{ marginBottom: 20 }}>
        <Col span={8}>
          <StatCard title={t('overview.totalCollections')} value={loading ? '—' : collections.length} icon={<TableOutlined />} color="#C07830" />
        </Col>
        <Col span={8}>
          <StatCard title={t('overview.totalDocs')} value={loading ? '—' : totalDocs.toLocaleString()} icon={<FileTextOutlined />} color="#3b82f6" />
        </Col>
        <Col span={8}>
          <StatCard
            title={t('overview.avgDocs')}
            value={loading || collections.length === 0 ? '—' : Math.round(totalDocs / collections.length).toLocaleString()}
            icon={<DatabaseOutlined />} color="#f59e0b"
          />
        </Col>
      </Row>

      <Card
        title={<Space><TableOutlined /><span>{t('overview.collectionList')}</span><Tag color="blue">{collections.length}</Tag></Space>}
        extra={<Button type="primary" size="small" onClick={() => setCurrentNav('collections')}>{t('overview.manage')}</Button>}
      >
        {collections.length === 0 && !loading
          ? <Empty description={t('overview.empty')} />
          : <Table columns={columns} dataSource={collections} rowKey="name" loading={loading} pagination={{ pageSize: 5, size: 'small' }} size="small" />
        }
      </Card>
    </div>
  )
}
