import { useState } from 'react'
import { Button, Card, Form, Input, InputNumber, Space, Tag, Typography, Alert, Divider } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'
import type { QueryResultItem } from '../types'

export default function QueryPage() {
  const { activeConnId, activeCollection } = useAppStore()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<QueryResultItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [queried, setQueried] = useState(false)

  const handleQuery = async () => {
    if (!activeConnId || !activeCollection) return
    try {
      const values = await form.validateFields()
      const whereStr = values.where?.trim() || ''
      if (whereStr) {
        try { JSON.parse(whereStr) } catch { form.setFields([{ name: 'where', errors: ['请输入合法的 JSON'] }]); return }
      }
      setLoading(true)
      setError(null)
      const res = await bridge.query(activeConnId, activeCollection, values.query_text, values.n_results ?? 10, whereStr)
      if (res.error) { setError(res.error); setResults([]); return }
      setResults(res.items ?? [])
      setQueried(true)
    } catch {
      // validation
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <Typography.Title level={4} style={{ marginBottom: 16 }}>
        向量相似度查询 — <Typography.Text type="secondary" style={{ fontSize: 16 }}>{activeCollection}</Typography.Text>
      </Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical" initialValues={{ n_results: 10 }}>
          <Form.Item name="query_text" label="查询文本" rules={[{ required: true, message: '请输入查询文本' }]}>
            <Input.TextArea rows={3} placeholder="输入查询内容，ChromaDB 将返回最相似的文档..." />
          </Form.Item>
          <Space align="start" style={{ width: '100%' }} styles={{ item: { flex: 1 } }}>
            <Form.Item name="n_results" label="返回数量" style={{ width: 150 }}>
              <InputNumber min={1} max={100} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="where" label={<span>Where 过滤 <Typography.Text type="secondary" style={{ fontSize: 12 }}>（可选，JSON 格式）</Typography.Text></span>} style={{ flex: 1 }}>
              <Input placeholder='{"category": "news"}' style={{ fontFamily: 'monospace' }} />
            </Form.Item>
          </Space>
          <Button type="primary" icon={<SearchOutlined />} loading={loading} onClick={handleQuery}>
            开始查询
          </Button>
        </Form>
      </Card>

      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}

      {queried && results.length === 0 && !error && (
        <Alert type="info" message="没有找到相似文档" />
      )}

      {results.map((item, idx) => (
        <Card
          key={item.id}
          size="small"
          style={{ marginBottom: 8 }}
          title={
            <Space>
              <Tag color="purple">#{idx + 1}</Tag>
              <Typography.Text code style={{ fontSize: 12 }}>{item.id}</Typography.Text>
              {item.distance !== null && (
                <Tag color={item.distance < 0.3 ? 'green' : item.distance < 0.7 ? 'orange' : 'red'}>
                  距离 {item.distance.toFixed(4)}
                </Tag>
              )}
            </Space>
          }
        >
          <Typography.Paragraph style={{ marginBottom: 8, whiteSpace: 'pre-wrap' }}>
            {item.document}
          </Typography.Paragraph>
          {Object.keys(item.metadata).length > 0 && (
            <>
              <Divider style={{ margin: '8px 0' }} />
              <Space wrap>
                {Object.entries(item.metadata).map(([k, v]) => (
                  <Tag key={k}>{k}: {String(v)}</Tag>
                ))}
              </Space>
            </>
          )}
        </Card>
      ))}
    </div>
  )
}
