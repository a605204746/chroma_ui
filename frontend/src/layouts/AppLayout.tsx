import { useState } from 'react'
import {
  Layout, Button, Typography, Badge, Tooltip,
  message, theme, Avatar, Space, Tabs, Tag, Popover, Radio, Divider,
} from 'antd'
import {
  DatabaseOutlined, PlusOutlined, DisconnectOutlined,
  LinkOutlined, DeleteOutlined, EditOutlined,
  SunOutlined, MoonOutlined, AppstoreOutlined,
  TableOutlined, SettingOutlined, LaptopOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'
import type { ThemeMode } from '../store/appStore'
import type { Connection } from '../types'
import ConnectionModal from '../components/ConnectionModal'
import OverviewPage from '../pages/OverviewPage'
import CollectionsPage from '../pages/CollectionsPage'
import CollectionDetailPage from '../pages/CollectionDetailPage'

const { Sider, Content, Header } = Layout

function SettingsPopover() {
  const { themeMode, setThemeMode } = useAppStore()
  const { token } = theme.useToken()
  const { t, i18n } = useTranslation()

  const themeOptions: { value: ThemeMode; label: string; icon: React.ReactNode }[] = [
    { value: 'light', label: t('theme.light'), icon: <SunOutlined /> },
    { value: 'dark', label: t('theme.dark'), icon: <MoonOutlined /> },
    { value: 'system', label: t('theme.system'), icon: <LaptopOutlined /> },
  ]

  const changeLang = (lang: string) => {
    i18n.changeLanguage(lang)
    localStorage.setItem('chroma-ui-lang', lang)
  }

  return (
    <div style={{ width: 230 }}>
      <Typography.Text strong style={{ fontSize: 13 }}>{t('settings.appearance')}</Typography.Text>
      <div style={{ marginTop: 10 }}>
        <Radio.Group
          value={themeMode}
          onChange={e => setThemeMode(e.target.value)}
          style={{ display: 'flex', flexDirection: 'column', gap: 6 }}
        >
          {themeOptions.map(opt => (
            <Radio key={opt.value} value={opt.value}>
              <Space size={6}>
                <span style={{ color: themeMode === opt.value ? token.colorPrimary : token.colorTextSecondary }}>
                  {opt.icon}
                </span>
                <span>{opt.label}</span>
              </Space>
            </Radio>
          ))}
        </Radio.Group>
      </div>

      <Divider style={{ margin: '12px 0 8px' }} />

      <Typography.Text strong style={{ fontSize: 13 }}>{t('settings.language')}</Typography.Text>
      <div style={{ marginTop: 10 }}>
        <Radio.Group
          value={i18n.language}
          onChange={e => changeLang(e.target.value)}
          style={{ display: 'flex', gap: 8 }}
        >
          <Radio value="zh">{t('lang.zh')}</Radio>
          <Radio value="en">{t('lang.en')}</Radio>
        </Radio.Group>
      </div>

      <Divider style={{ margin: '12px 0 8px' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>Chroma UI</Typography.Text>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>v1.0.0</Typography.Text>
      </div>
    </div>
  )
}

export default function AppLayout() {
  const {
    connections, activeConnId, currentNav,
    setConnections, setActiveConnId, setCollections, setCurrentNav,
    updateConnectionStatus, backToCollections,
  } = useAppStore()
  const { t } = useTranslation()

  const [connModalOpen, setConnModalOpen] = useState(false)
  const [editingConn, setEditingConn] = useState<Connection | null>(null)
  const { token } = theme.useToken()

  const handleConnect = async (id: string) => {
    const res = await bridge.connect(id)
    if (!res.success) { message.error(t('conn.connectFailed', { msg: res.error })); return }
    updateConnectionStatus(id, true)
    setActiveConnId(id)
    const cols = await bridge.listCollections(id)
    setCollections(Array.isArray(cols) ? cols : [])
    message.success(t('conn.connected'))
  }

  const handleDisconnect = async (id: string) => {
    await bridge.disconnect(id)
    updateConnectionStatus(id, false)
    if (activeConnId === id) { setActiveConnId(null); setCollections([]) }
  }

  const handleRemoveConn = async (id: string) => {
    await bridge.removeConnection(id)
    const conns = await bridge.getConnections()
    setConnections(conns)
    if (activeConnId === id) setActiveConnId(null)
  }

  const openEdit = (conn: Connection) => { setEditingConn(conn); setConnModalOpen(true) }
  const openAdd = () => { setEditingConn(null); setConnModalOpen(true) }
  const closeModal = () => { setConnModalOpen(false); setEditingConn(null) }

  const handleTabChange = (key: string) => {
    if (key === 'collections') backToCollections()
    else setCurrentNav(key as any)
  }

  const activeTabKey = currentNav === 'collection-detail' ? 'collections' : currentNav

  const renderContent = () => {
    if (!activeConnId) return <OverviewPage onAddConnection={openAdd} />
    switch (currentNav) {
      case 'overview': return <OverviewPage onAddConnection={openAdd} />
      case 'collections': return <CollectionsPage />
      case 'collection-detail': return <CollectionDetailPage />
      default: return <OverviewPage onAddConnection={openAdd} />
    }
  }

  const connTypeLabel = (conn: Connection) =>
    conn.conn_type === 'persistent' ? t('conn.localDir') : t('conn.http')

  const connTypeColor = (conn: Connection) =>
    conn.conn_type === 'persistent' ? 'orange' : 'blue'

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 20px', background: token.colorBgContainer,
        borderBottom: `1px solid ${token.colorBorderSecondary}`,
        height: 52, zIndex: 10,
      }}>
        <Space size={10}>
          <Avatar size={26} style={{ background: '#8b5cf6', flexShrink: 0 }} icon={<DatabaseOutlined />} />
          <Typography.Text strong style={{ fontSize: 15, letterSpacing: -0.3 }}>Chroma UI</Typography.Text>
        </Space>
        <Popover content={<SettingsPopover />} title={null} trigger="click" placement="bottomRight" arrow={false}>
          <Tooltip title={t('settings.title')}>
            <Button type="text" icon={<SettingOutlined />} />
          </Tooltip>
        </Popover>
      </Header>

      <Layout>
        <Sider width={220} style={{
          background: token.colorBgContainer,
          borderRight: `1px solid ${token.colorBorderSecondary}`,
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '12px 16px 8px',
            borderBottom: `1px solid ${token.colorBorderSecondary}`,
          }}>
            <Typography.Text strong style={{ fontSize: 13 }}>{t('conn.title')}</Typography.Text>
            <Tooltip title={t('conn.addTip')}>
              <Button size="small" type="primary" icon={<PlusOutlined />} onClick={openAdd} />
            </Tooltip>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 8px' }}>
            {connections.length === 0 && (
              <div style={{ padding: '24px 8px', textAlign: 'center' }}>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>{t('conn.empty')}</Typography.Text>
              </div>
            )}
            {connections.map(conn => {
              const isActive = conn.id === activeConnId
              return (
                <div
                  key={conn.id}
                  onClick={() => conn.connected ? setActiveConnId(conn.id) : handleConnect(conn.id)}
                  style={{
                    borderRadius: 8, marginBottom: 4,
                    border: `1px solid ${isActive ? token.colorPrimary : token.colorBorderSecondary}`,
                    background: isActive ? token.colorPrimaryBg : token.colorBgContainer,
                    overflow: 'hidden', cursor: 'pointer', padding: '8px 10px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <Badge status={conn.connected ? 'success' : 'default'} />
                    <Typography.Text
                      ellipsis strong={isActive}
                      style={{ flex: 1, fontSize: 13, color: isActive ? token.colorPrimary : token.colorText }}
                    >
                      {conn.name}
                    </Typography.Text>
                    <Tag color={connTypeColor(conn)} style={{ fontSize: 10, padding: '0 4px', lineHeight: '16px', margin: 0 }}>
                      {connTypeLabel(conn)}
                    </Tag>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                    <Tooltip title={conn.connected ? t('conn.disconnect') : t('conn.connect')}>
                      <Button
                        size="small" type="text"
                        icon={conn.connected ? <DisconnectOutlined /> : <LinkOutlined />}
                        onClick={e => { e.stopPropagation(); conn.connected ? handleDisconnect(conn.id) : handleConnect(conn.id) }}
                        style={{ color: conn.connected ? token.colorError : token.colorSuccess }}
                      />
                    </Tooltip>
                    <Tooltip title={t('conn.edit')}>
                      <Button size="small" type="text" icon={<EditOutlined />}
                        onClick={e => { e.stopPropagation(); openEdit(conn) }} />
                    </Tooltip>
                    <Tooltip title={t('conn.delete')}>
                      <Button size="small" type="text" danger icon={<DeleteOutlined />}
                        onClick={e => { e.stopPropagation(); handleRemoveConn(conn.id) }} />
                    </Tooltip>
                  </div>
                </div>
              )
            })}
          </div>
        </Sider>

        <Layout style={{ background: token.colorBgLayout }}>
          {activeConnId && (
            <div style={{
              background: token.colorBgContainer,
              borderBottom: `1px solid ${token.colorBorderSecondary}`,
              padding: '0 24px',
            }}>
              <Tabs
                activeKey={activeTabKey}
                onChange={handleTabChange}
                size="small"
                style={{ marginBottom: 0 }}
                items={[
                  { key: 'overview', label: <Space size={4}><AppstoreOutlined />{t('nav.overview')}</Space> },
                  { key: 'collections', label: <Space size={4}><TableOutlined />{t('nav.collections')}</Space> },
                ]}
              />
            </div>
          )}
          <Content style={{ padding: 24, overflow: 'auto' }}>
            {renderContent()}
          </Content>
        </Layout>
      </Layout>

      <ConnectionModal open={connModalOpen} editingConn={editingConn} onClose={closeModal} />
    </Layout>
  )
}
