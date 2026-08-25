import { useState } from 'react'
import {
  Button, Card, Form, Input, InputNumber, Space,
  Tag, Typography, Alert, Divider, Collapse, Empty,
} from 'antd'
import { SearchOutlined, FilterOutlined, ApartmentOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { queryApi } from '../api'
import { useAppStore } from '../store/appStore'
import type { QueryResultItem } from '../types'
import FilterBuilder, { buildWhereJson } from '../components/FilterBuilder'
import type { FilterRow } from '../components/FilterBuilder'

interface Props {
  hasEmbedding: boolean
  onConfigEmbed: () => void
  embModel?: string
}

export default function SearchTab({ hasEmbedding, onConfigEmbed, embModel }: Props) {
  const { activeConnId, activeCollection } = useAppStore()
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<QueryResultItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [queried, setQueried] = useState(false)
  const [filterRows, setFilterRows] = useState<FilterRow[]>([])

  const handleQuery = async () => {
    if (!activeConnId || !activeCollection) return
    try {
      const values = await form.validateFields()
      const whereJson = buildWhereJson(filterRows)
      setLoading(true)
      setError(null)
      const res = await queryApi.query(activeConnId, activeCollection, values.query_text, values.n_results ?? 10, whereJson)
      if (res.error) { setError(res.error); setResults([]); return }
      setResults(res.items ?? [])
      setQueried(true)
    } catch {
      // validation
    } finally {
      setLoading(false)
    }
  }

  const getDistanceColor = (d: number | null) => {
    if (d === null) return 'default'
    if (d < 0.3) return '#22c55e'
    if (d < 0.7) return '#f59e0b'
    return '#ef4444'
  }

  return (
    <div>
      {!hasEmbedding && (
        <Alert
          type="error"
          showIcon
          icon={<ApartmentOutlined />}
          style={{ marginBottom: 16 }}
          message={t('search.noEmbedTitle')}
          description={
            <Space>
              <span>{t('search.noEmbedDesc')}</span>
              <Button type="primary" size="small" onClick={onConfigEmbed}>{t('search.configure')}</Button>
            </Space>
          }
        />
      )}
      {hasEmbedding && (
        <Alert
          type="success"
          showIcon
          style={{ marginBottom: 16 }}
          message={<Space size={6}><span>{t('search.model')}</span><Tag color="purple" style={{ fontFamily: 'monospace' }}>{embModel}</Tag></Space>}
        />
      )}

      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical" initialValues={{ n_results: 10 }}>
          <Form.Item name="query_text" label={t('search.queryText')} rules={[{ required: true, message: t('search.queryText') }]}>
            <Input.TextArea
              rows={3}
              placeholder={t('search.placeholder')}
              style={{ resize: 'none' }}
            />
          </Form.Item>

          <Space align="start">
            <Form.Item name="n_results" label={t('search.nResults')} style={{ width: 120, marginBottom: 0 }}>
              <InputNumber min={1} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </Space>

          <Collapse
            ghost
            style={{ marginTop: 12, marginBottom: 12 }}
            items={[{
              key: 'filter',
              label: <Space><FilterOutlined /><span>{t('search.filter')}</span>{filterRows.length > 0 && <Tag color="purple">{t('search.conditions', { n: filterRows.length })}</Tag>}</Space>,
              children: <FilterBuilder rows={filterRows} onChange={setFilterRows} />,
            }]}
          />

          <Button
            type="primary"
            icon={<SearchOutlined />}
            loading={loading}
            onClick={handleQuery}
            disabled={!hasEmbedding}
            block
          >
            {hasEmbedding ? t('search.startSearch') : t('search.requireEmbed')}
          </Button>
        </Form>
      </Card>

      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}

      {queried && results.length === 0 && !error && (
        <Empty description={t('search.noResult')} />
      )}

      {results.length > 0 && (
        <div>
          <Typography.Text type="secondary" style={{ fontSize: 12, marginBottom: 8, display: 'block' }}>
            {t('search.found', { n: results.length })}
          </Typography.Text>
          {results.map((item, idx) => (
            <Card
              key={item.id}
              size="small"
              style={{ marginBottom: 8, borderLeft: `3px solid ${getDistanceColor(item.distance)}` }}
              title={
                <Space>
                  <Tag color="purple" style={{ fontFamily: 'monospace' }}>#{idx + 1}</Tag>
                  <Typography.Text code style={{ fontSize: 12 }} copyable>{item.id}</Typography.Text>
                  {item.distance !== null && (
                    <Tag color={item.distance < 0.3 ? 'success' : item.distance < 0.7 ? 'warning' : 'error'}>
                      {t('search.similarity')} {(1 - item.distance).toFixed(4)}
                    </Tag>
                  )}
                </Space>
              }
            >
              <Typography.Paragraph
                style={{ marginBottom: 8, whiteSpace: 'pre-wrap' }}
                ellipsis={{ rows: 3, expandable: true, symbol: t('search.expand') }}
              >
                {item.document}
              </Typography.Paragraph>
              {Object.keys(item.metadata ?? {}).length > 0 && (
                <>
                  <Divider style={{ margin: '8px 0' }} />
                  <Space wrap size={4}>
                    {Object.entries(item.metadata ?? {}).map(([k, v]) => (
                      <Tag key={k} style={{ fontSize: 11 }}>{k}: {String(v)}</Tag>
                    ))}
                  </Space>
                </>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
