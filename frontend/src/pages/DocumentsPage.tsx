import { useEffect, useState, useCallback } from 'react'
import { Table, Button, Space, Popconfirm, message, Typography, Tag } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { Document } from '../types'
import { documentApi } from '../api'
import { useAppStore } from '../store/appStore'
import DocumentModal from '../components/DocumentModal'

const PAGE_SIZE = 20

export default function DocumentsPage() {
  const { activeConnId, activeCollection } = useAppStore()
  const [loading, setLoading] = useState(false)
  const [docs, setDocs] = useState<Document[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editDoc, setEditDoc] = useState<Document | null>(null)

  const loadDocs = useCallback(async (p = page) => {
    if (!activeConnId || !activeCollection) return
    setLoading(true)
    try {
      const res = await documentApi.getDocuments(activeConnId, activeCollection, PAGE_SIZE, (p - 1) * PAGE_SIZE)
      if (res.error) { message.error(res.error); return }
      setDocs(res.items ?? [])
      setTotal(res.total ?? 0)
    } finally {
      setLoading(false)
    }
  }, [activeConnId, activeCollection, page])

  useEffect(() => { setPage(1); loadDocs(1) }, [activeConnId, activeCollection])
  useEffect(() => { loadDocs() }, [page])

  const handleDelete = async (id: string) => {
    if (!activeConnId || !activeCollection) return
    const res = await documentApi.deleteDocument(activeConnId, activeCollection, id)
    if (res.error || res.success === false) { message.error(res.error || '删除失败'); return }
    message.success('文档已删除')
    loadDocs()
  }

  const openEdit = (doc: Document) => { setEditDoc(doc); setModalOpen(true) }
  const openAdd = () => { setEditDoc(null); setModalOpen(true) }

  const columns: ColumnsType<Document> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 200,
      ellipsis: true,
      render: (id: string) => <Typography.Text code style={{ fontSize: 12 }}>{id}</Typography.Text>,
    },
    {
      title: 'Document',
      dataIndex: 'document',
      key: 'document',
      ellipsis: true,
      render: (doc: string) => <Typography.Text>{doc}</Typography.Text>,
    },
    {
      title: 'Metadata',
      dataIndex: 'metadata',
      key: 'metadata',
      width: 200,
      render: (meta: Record<string, unknown>) => {
        const keys = Object.keys(meta)
        if (keys.length === 0) return <Typography.Text type="secondary">—</Typography.Text>
        return keys.slice(0, 3).map(k => (
          <Tag key={k} style={{ marginBottom: 2 }}>{k}: {String(meta[k])}</Tag>
        ))
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button size="small" type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>编辑</Button>
          <Popconfirm
            title="确认删除此文档？"
            onConfirm={() => handleDelete(record.id)}
            okText="删除"
            okType="danger"
            cancelText="取消"
          >
            <Button size="small" type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Space>
          <Typography.Title level={4} style={{ margin: 0 }}>{activeCollection}</Typography.Title>
          <Tag color="blue">{total.toLocaleString()} 条文档</Tag>
        </Space>
        <Space>
          <Button onClick={() => loadDocs()} loading={loading}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openAdd}>新增文档</Button>
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={docs}
        rowKey="id"
        loading={loading}
        pagination={{
          current: page,
          pageSize: PAGE_SIZE,
          total,
          onChange: (p) => setPage(p),
          showTotal: (t) => `共 ${t} 条`,
          showSizeChanger: false,
        }}
      />
      <DocumentModal
        open={modalOpen}
        doc={editDoc}
        onClose={() => setModalOpen(false)}
        onSaved={() => loadDocs()}
      />
    </div>
  )
}
