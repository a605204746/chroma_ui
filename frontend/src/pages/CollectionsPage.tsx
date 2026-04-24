import { useEffect, useState } from 'react'
import { Table, Button, Space, Popconfirm, message, Typography, Tag, Card, Input } from 'antd'
import { PlusOutlined, DeleteOutlined, SearchOutlined, ReloadOutlined, EditOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import type { ColumnsType } from 'antd/es/table'
import type { Collection } from '../types'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'
import CollectionModal from '../components/CollectionModal'

export default function CollectionsPage() {
  const { activeConnId, collections, setCollections, navigateToCollection } = useAppStore()
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editCollection, setEditCollection] = useState<Collection | null>(null)
  const [search, setSearch] = useState('')

  const loadCollections = async () => {
    if (!activeConnId) return
    setLoading(true)
    try {
      const cols = await bridge.listCollections(activeConnId)
      setCollections(Array.isArray(cols) ? cols : [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadCollections() }, [activeConnId])

  const handleDelete = async (name: string) => {
    if (!activeConnId) return
    const res = await bridge.deleteCollection(activeConnId, name)
    if (res.success === false || res.error) { message.error(res.error || t('collections.deleteFailed')); return }
    message.success(t('collections.deleteSuccess', { name }))
    loadCollections()
  }

  const openCreate = () => { setEditCollection(null); setModalOpen(true) }
  const openEdit = (col: Collection) => { setEditCollection(col); setModalOpen(true) }

  const filtered = collections.filter(c => c.name.toLowerCase().includes(search.toLowerCase()))

  const columns: ColumnsType<Collection> = [
    {
      title: t('collections.colName'), dataIndex: 'name', key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (name: string) => (
        <Typography.Link strong onClick={() => navigateToCollection(name)}>{name}</Typography.Link>
      ),
    },
    {
      title: t('collections.docCount'), dataIndex: 'count', key: 'count', width: 120,
      sorter: (a, b) => a.count - b.count,
      render: (count: number) => <Tag color="blue" style={{ fontFamily: 'monospace' }}>{count.toLocaleString()}</Tag>,
    },
    {
      title: 'Metadata', dataIndex: 'metadata', key: 'metadata',
      render: (meta: Record<string, unknown>) => {
        const keys = Object.keys(meta ?? {})
        return keys.length === 0
          ? <Typography.Text type="secondary">—</Typography.Text>
          : <Typography.Text code style={{ fontSize: 12 }}>{JSON.stringify(meta)}</Typography.Text>
      },
    },
    {
      title: t('collections.action'), key: 'action', width: 160,
      render: (_, record) => (
        <Space>
          <Button size="small" type="link" onClick={() => navigateToCollection(record.name)}>{t('collections.view')}</Button>
          <Button size="small" type="text" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          <Popconfirm
            title={t('collections.deleteConfirm', { name: record.name })}
            description={t('collections.deleteDesc')}
            onConfirm={() => handleDelete(record.name)}
            okText={t('common.delete', { defaultValue: t('collections.deleteConfirm').slice(0, 2) })}
            okType="danger"
            cancelText={t('connModal.cancel')}
          >
            <Button size="small" type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <Typography.Title level={4} style={{ margin: 0 }}>{t('collections.title')}</Typography.Title>
          <Typography.Text type="secondary">{t('collections.count', { n: collections.length })}</Typography.Text>
        </div>
        <Space>
          <Input
            prefix={<SearchOutlined />} placeholder={t('collections.searchPlaceholder')}
            value={search} onChange={e => setSearch(e.target.value)} style={{ width: 200 }} allowClear
          />
          <Button icon={<ReloadOutlined />} onClick={loadCollections} loading={loading} />
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            {t('collections.create')}
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns} dataSource={filtered} rowKey="name" loading={loading}
          pagination={{ pageSize: 15, showTotal: n => t('collections.total', { n }) }}
          locale={{ emptyText: t('collections.empty') }}
        />
      </Card>

      <CollectionModal
        open={modalOpen}
        editCollection={editCollection}
        onClose={() => setModalOpen(false)}
        onSaved={loadCollections}
      />
    </div>
  )
}
