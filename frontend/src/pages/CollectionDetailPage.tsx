import { useState, useEffect } from 'react'
import { Tabs, Button, Space, Typography, Popconfirm, message, Tag, theme, Modal } from 'antd'
import {
  TableOutlined, ApartmentOutlined, SearchOutlined,
  DeleteOutlined, ArrowLeftOutlined, ReloadOutlined,
} from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { collectionApi, embeddingApi } from '../api'
import { useAppStore } from '../store/appStore'
import DataTab from '../tabs/DataTab'
import SchemaTab from '../tabs/SchemaTab'
import SearchTab from '../tabs/SearchTab'
import EmbeddingConfigModal from '../components/EmbeddingConfigModal'
import type { EmbeddingConfig } from '../types'

export default function CollectionDetailPage() {
  const { activeConnId, activeCollection, collections, setCollections, backToCollections } = useAppStore()
  const { token } = theme.useToken()
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState('data')
  const [embModalOpen, setEmbModalOpen] = useState(false)
  const [embCfg, setEmbCfg] = useState<EmbeddingConfig | null>(null)
  const colInfo = collections.find(c => c.name === activeCollection)

  const loadEmbCfg = () => {
    if (!activeConnId || !activeCollection) return
    embeddingApi.getCollectionEmbedding(activeConnId, activeCollection).then(cfg => setEmbCfg(cfg))
  }

  useEffect(() => { loadEmbCfg() }, [activeConnId, activeCollection])

  const hasEmbedding = !!(embCfg?.embedding_url && embCfg?.embedding_model)

  const handleTabChange = (key: string) => {
    setActiveTab(key)
    if (key === 'search' && !hasEmbedding) {
      Modal.warning({
        title: t('collection.noVector'),
        content: t('search.noEmbedDesc'),
        okText: t('data.configure'),
        onOk: () => setEmbModalOpen(true),
      })
    }
  }

  const handleDelete = async () => {
    if (!activeConnId || !activeCollection) return
    const res = await collectionApi.deleteCollection(activeConnId, activeCollection)
    if (res.success === false || res.error) { message.error(res.error || t('collection.deleteFailed')); return }
    message.success(t('collection.deleteSuccess', { name: activeCollection }))
    const cols = await collectionApi.listCollections(activeConnId)
    setCollections(Array.isArray(cols) ? cols : [])
    backToCollections()
  }

  const handleRefresh = async () => {
    if (!activeConnId) return
    const cols = await collectionApi.listCollections(activeConnId)
    setCollections(Array.isArray(cols) ? cols : [])
  }

  const tabItems = [
    { key: 'data', label: <Space><TableOutlined />{t('collection.dataTab')}</Space>, children: <DataTab onConfigEmbed={() => setEmbModalOpen(true)} hasEmbedding={hasEmbedding} /> },
    { key: 'schema', label: <Space><ApartmentOutlined />{t('collection.schemaTab')}</Space>, children: <SchemaTab /> },
    { key: 'search', label: <Space><SearchOutlined />{t('collection.searchTab')}</Space>, children: <SearchTab onConfigEmbed={() => setEmbModalOpen(true)} hasEmbedding={hasEmbedding} embModel={embCfg?.embedding_model} /> },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <Space align="start">
          <Button icon={<ArrowLeftOutlined />} type="text" onClick={backToCollections} />
          <div>
            <Space>
              <Typography.Title level={4} style={{ margin: 0 }}>{activeCollection}</Typography.Title>
              {colInfo && <Tag color="blue">{colInfo.count.toLocaleString()}</Tag>}
              {hasEmbedding
                ? <Tag color="green" icon={<ApartmentOutlined />}>
                    {embCfg!.embedding_model}
                    {embCfg!.dimension ? <span style={{ opacity: 0.75 }}> · {embCfg!.dimension}{t('embed.dimensionUnit')}</span> : ''}
                  </Tag>
                : <Tag color="orange" icon={<ApartmentOutlined />} style={{ cursor: 'pointer' }} onClick={() => setEmbModalOpen(true)}>
                    {t('collection.noVector')}
                  </Tag>
              }
            </Space>
            <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block' }}>{t('collection.detail')}</Typography.Text>
          </div>
        </Space>

        <Space>
          <Button icon={<ApartmentOutlined />} onClick={() => setEmbModalOpen(true)}>
            {hasEmbedding ? t('collection.vectorModel') : t('collection.configVector')}
          </Button>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>{t('collection.refresh')}</Button>
          <Popconfirm
            title={t('collection.deleteConfirm', { name: activeCollection })}
            description={t('collection.deleteDesc')}
            onConfirm={handleDelete}
            okText={t('collection.deleteCollection')} okType="danger" cancelText={t('connModal.cancel')}
          >
            <Button danger icon={<DeleteOutlined />}>{t('collection.deleteCollection')}</Button>
          </Popconfirm>
        </Space>
      </div>

      <Tabs
        activeKey={activeTab} onChange={handleTabChange} items={tabItems}
        style={{ background: token.colorBgContainer, padding: '0 16px', borderRadius: 8 }}
      />

      <EmbeddingConfigModal
        open={embModalOpen} onClose={() => setEmbModalOpen(false)}
        onSaved={() => { loadEmbCfg(); handleRefresh() }}
      />
    </div>
  )
}
