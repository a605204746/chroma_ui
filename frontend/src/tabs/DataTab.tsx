import { useEffect, useState, useCallback } from 'react'
import {
  Table, Button, Space, Popconfirm, message, Typography, Tag,
  Input, Switch, Modal, theme, Tooltip, Alert,
} from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, SearchOutlined, ApartmentOutlined, CodeOutlined, ThunderboltOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import type { ColumnsType } from 'antd/es/table'
import type { Document } from '../types'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'
import DocumentModal from '../components/DocumentModal'

const PAGE_SIZE = 20

interface Props {
  hasEmbedding: boolean
  onConfigEmbed: () => void
}

export default function DataTab({ hasEmbedding, onConfigEmbed }: Props) {
  const { activeConnId, activeCollection } = useAppStore()
  const { token } = theme.useToken()
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [docs, setDocs] = useState<Document[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [editDoc, setEditDoc] = useState<Document | null>(null)
  const [showEmbedding, setShowEmbedding] = useState(false)
  const [embViewDoc, setEmbViewDoc] = useState<Document | null>(null)
  const [metaViewDoc, setMetaViewDoc] = useState<Document | null>(null)
  const [seeding, setSeeding] = useState(false)

  const loadDocs = useCallback(async (p = page, withEmb = showEmbedding) => {
    if (!activeConnId || !activeCollection) return
    setLoading(true)
    try {
      const res = await bridge.getDocuments(activeConnId, activeCollection, PAGE_SIZE, (p - 1) * PAGE_SIZE, withEmb)
      if (res.error) { message.error(res.error); return }
      setDocs(res.items ?? [])
      setTotal(res.total ?? 0)
    } finally {
      setLoading(false)
    }
  }, [activeConnId, activeCollection, page, showEmbedding])

  useEffect(() => { setPage(1); loadDocs(1, showEmbedding) }, [activeConnId, activeCollection])
  useEffect(() => { loadDocs(page, showEmbedding) }, [page])

  const handleToggleEmbedding = (val: boolean) => { setShowEmbedding(val); loadDocs(page, val) }

  const handleDelete = async (id: string) => {
    if (!activeConnId || !activeCollection) return
    const res = await bridge.deleteDocument(activeConnId, activeCollection, id)
    if (res.error || res.success === false) { message.error(res.error || t('data.deleteFailed')); return }
    message.success(t('data.deleteSuccess'))
    loadDocs()
  }

  const handleAddClick = () => {
    if (!hasEmbedding) {
      Modal.warning({
        title: t('data.requireEmbed'),
        content: t('data.requireEmbedDesc'),
        okText: t('data.configure'),
        onOk: onConfigEmbed,
      })
      return
    }
    setEditDoc(null)
    setModalOpen(true)
  }

  const handleSeed = () => {
    if (!hasEmbedding) {
      Modal.warning({
        title: t('data.requireEmbed'),
        content: t('data.requireEmbedDesc'),
        okText: t('data.configure'),
        onOk: onConfigEmbed,
      })
      return
    }
    Modal.confirm({
      title: t('data.seedBtn'),
      content: t('data.seedConfirm'),
      okText: t('data.seedBtn'),
      cancelText: t('connModal.cancel'),
      onOk: async () => {
        if (!activeConnId || !activeCollection) return
        setSeeding(true)
        try {
          const res = await bridge.seedTestData(activeConnId, activeCollection)
          if (res.error || res.success === false) { message.error(res.error); return }
          message.success(t('data.seedSuccess', { n: res.count }))
          loadDocs(1, showEmbedding)
        } finally {
          setSeeding(false)
        }
      },
    })
  }

  const copyText = (text: string, successMsg: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => message.success(successMsg))
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      message.success(successMsg)
    }
  }

  const filtered = search
    ? docs.filter(d => d.id.includes(search) || d.document.includes(search))
    : docs

  const embeddingCol: ColumnsType<Document>[number] = {
    title: 'Embedding',
    dataIndex: 'embedding',
    key: 'embedding',
    width: 180,
    render: (emb: number[] | null | undefined, record: Document) => {
      if (!emb || emb.length === 0) return <Typography.Text type="secondary">—</Typography.Text>
      const fmt = (v: number, d: number) => (typeof v === 'number' && isFinite(v)) ? v.toFixed(d) : String(v)
      const preview = emb.slice(0, 4).map(v => fmt(v, 4)).join(', ')
      return (
        <Space size={4} style={{ flexWrap: 'nowrap', whiteSpace: 'nowrap' }}>
          <Tag color="purple" style={{ fontFamily: 'monospace', fontSize: 11, margin: 0 }}>{emb.length}d</Tag>
          <Typography.Text type="secondary" style={{ fontSize: 11, fontFamily: 'monospace', whiteSpace: 'nowrap' }}>{preview}…</Typography.Text>
          <Button
            size="small" type="text" icon={<ApartmentOutlined style={{ fontSize: 11 }} />}
            style={{ padding: '0 2px', height: 18, flexShrink: 0 }}
            onClick={() => setEmbViewDoc(record)}
          />
        </Space>
      )
    },
  }

  const baseColumns: ColumnsType<Document> = [
    {
      title: 'ID', dataIndex: 'id', key: 'id', width: 160, ellipsis: { showTitle: false },
      render: (id: string) => (
        <Tooltip title={id} placement="topLeft">
          <Typography.Text code copyable={{ tooltips: false }} style={{ fontSize: 12 }}>{id}</Typography.Text>
        </Tooltip>
      ),
    },
    {
      title: 'Document', dataIndex: 'document', key: 'document', width: 420,
      ellipsis: { showTitle: false },
      render: (doc: string) => (
        <Typography.Text copyable={{ text: doc, tooltips: false }} style={{ fontSize: 13, whiteSpace: 'nowrap' }}>
          {doc.length > 35 ? doc.slice(0, 35) + '…' : doc}
        </Typography.Text>
      ),
    },
    {
      title: 'Metadata', dataIndex: 'metadata', key: 'metadata', width: 200,
      render: (meta: Record<string, unknown> | null | undefined, record: Document) => {
        const entries = Object.entries(meta ?? {})
        if (entries.length === 0) return <Typography.Text type="secondary">—</Typography.Text>
        const tagColor = (v: unknown) => {
          if (v === null || v === undefined) return 'default'
          if (typeof v === 'boolean') return 'orange'
          if (typeof v === 'number') return 'green'
          return 'blue'
        }
        return (
          <Space size={4} style={{ flexWrap: 'nowrap' }}>
            {entries.slice(0, 2).map(([k, v]) => (
              <Tag key={k} color={tagColor(v)} style={{ fontSize: 11 }}>{k}: {String(v)}</Tag>
            ))}
            <Button
              size="small" type="text" icon={<CodeOutlined style={{ fontSize: 11 }} />}
              style={{ padding: '0 2px', height: 20, flexShrink: 0 }}
              onClick={() => setMetaViewDoc(record)}
            />
          </Space>
        )
      },
    },
  ]

  const actionCol: ColumnsType<Document>[number] = {
    title: t('collections.action'), key: 'action', width: 80, fixed: 'right',
    render: (_, record) => (
      <Space>
        <Button size="small" type="text" icon={<EditOutlined />} onClick={() => { setEditDoc(record); setModalOpen(true) }} />
        <Popconfirm title={t('data.deleteConfirm')} onConfirm={() => handleDelete(record.id)} okText={t('collection.deleteCollection').slice(0, 2)} okType="danger" cancelText={t('connModal.cancel')}>
          <Button size="small" type="text" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      </Space>
    ),
  }

  const columns: ColumnsType<Document> = showEmbedding
    ? [...baseColumns, embeddingCol, actionCol]
    : [...baseColumns, actionCol]

  return (
    <div>
      {!hasEmbedding && (
        <Alert
          type="warning" showIcon style={{ marginBottom: 12 }}
          message={t('data.noEmbed')}
          description={<span>{t('data.noEmbedDesc')}<Button type="link" size="small" style={{ padding: 0 }} onClick={onConfigEmbed}>{t('data.configure')}</Button></span>}
        />
      )}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Tag color="blue">{t('data.total', { n: total.toLocaleString() })}</Tag>
          <Space size={6}>
            <Switch size="small" checked={showEmbedding} onChange={handleToggleEmbedding} loading={loading} />
            <Typography.Text style={{ fontSize: 13 }}>{t('data.showVec')}</Typography.Text>
          </Space>
        </Space>
        <Space>
          <Input
            prefix={<SearchOutlined />} placeholder={t('data.searchPlaceholder')}
            value={search} onChange={e => setSearch(e.target.value)} style={{ width: 220 }} allowClear
          />
          <Button onClick={() => loadDocs()} loading={loading}>{t('data.refresh')}</Button>
          <Button icon={<ThunderboltOutlined />} onClick={handleSeed} loading={seeding}>{t('data.seedBtn')}</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAddClick}>{t('data.addDoc')}</Button>
        </Space>
      </div>

      <Table
        columns={columns} dataSource={filtered} rowKey="id" loading={loading} size="small"
        scroll={{ x: 'max-content' }}
        pagination={{
          current: page, pageSize: PAGE_SIZE, total,
          onChange: p => setPage(p),
          showTotal: n => t('data.rowTotal', { n }),
          showSizeChanger: false,
        }}
      />

      <DocumentModal open={modalOpen} doc={editDoc} onClose={() => setModalOpen(false)} onSaved={() => loadDocs()} />

      <Modal
        title={<Space><ApartmentOutlined /><span>{t('data.vecModal')}</span>{embViewDoc?.embedding && <Tag color="purple">{embViewDoc.embedding.length} {t('embed.dimensionUnit')}</Tag>}</Space>}
        open={!!embViewDoc} onCancel={() => setEmbViewDoc(null)} footer={null} width={640}
      >
        {embViewDoc?.embedding && (
          <div>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>ID: {embViewDoc.id}</Typography.Text>
            <div style={{
              marginTop: 12, background: token.colorFillAlter, borderRadius: 6,
              padding: '12px 16px', maxHeight: 400, overflowY: 'auto',
              fontFamily: 'monospace', fontSize: 12, lineHeight: 1.8, wordBreak: 'break-all',
            }}>
              {'['}
              {embViewDoc.embedding.map((v, i) => (
                <span key={i}>
                  <span style={{ color: token.colorPrimary }}>{v.toFixed(6)}</span>
                  {i < embViewDoc.embedding!.length - 1 ? ', ' : ''}
                </span>
              ))}
              {']'}
            </div>
            <div style={{ marginTop: 8, textAlign: 'right' }}>
              <Button size="small" onClick={() => copyText(JSON.stringify(embViewDoc.embedding), t('data.allCopied'))}>
                {t('data.copyVec')}
              </Button>
            </div>
          </div>
        )}
      </Modal>
      <Modal
        title={<Space><CodeOutlined /><span>{t('data.metaModal')}</span></Space>}
        open={!!metaViewDoc} onCancel={() => setMetaViewDoc(null)} footer={null} width={520}
      >
        {metaViewDoc && (
          <div>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>ID: {metaViewDoc.id}</Typography.Text>
            <div style={{
              marginTop: 12, background: token.colorFillAlter, borderRadius: 6,
              padding: '12px 16px', maxHeight: 400, overflowY: 'auto',
              fontFamily: 'monospace', fontSize: 13, lineHeight: 1.8, wordBreak: 'break-all',
            }}>
              {JSON.stringify(metaViewDoc.metadata ?? {}, null, 2)}
            </div>
            <div style={{ marginTop: 8, textAlign: 'right' }}>
              <Button size="small" onClick={() => copyText(JSON.stringify(metaViewDoc.metadata ?? {}), t('data.allCopied'))}>
                {t('data.copyMeta')}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
