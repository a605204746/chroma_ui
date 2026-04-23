import { useEffect, useState } from 'react'
import { Tag, Typography, Spin, Card, Descriptions } from 'antd'
import { useTranslation } from 'react-i18next'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'

export default function SchemaTab() {
  const { activeConnId, activeCollection, collections } = useAppStore()
  const { t } = useTranslation()
  const [loading, setLoading] = useState(false)
  const [embDim, setEmbDim] = useState<number | null | undefined>(undefined)
  const colInfo = collections.find(c => c.name === activeCollection)

  useEffect(() => {
    if (!activeConnId || !activeCollection) return
    setLoading(true)
    setEmbDim(undefined)
    bridge.getEmbeddingInfo(activeConnId, activeCollection)
      .then(res => setEmbDim(res.error ? null : (res.dimension ?? null)))
      .finally(() => setLoading(false))
  }, [activeConnId, activeCollection])

  const metaEntries = Object.entries(colInfo?.metadata ?? {})

  return (
    <div>
      {loading
        ? <Spin />
        : colInfo && (
          <Card size="small">
            <Descriptions column={1} size="small" labelStyle={{ width: 140, color: 'var(--ant-color-text-secondary)', fontWeight: 500 }}>
              <Descriptions.Item label={t('schema.colName')}>
                <Typography.Text strong copyable={{ tooltips: false }}>{colInfo.name}</Typography.Text>
              </Descriptions.Item>
              <Descriptions.Item label={t('schema.total')}>
                <Tag color="blue">{colInfo.count.toLocaleString()}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label={t('schema.dimension')}>
                {embDim === undefined
                  ? <Typography.Text type="secondary">{t('schema.loading')}</Typography.Text>
                  : embDim === null
                    ? <Typography.Text type="secondary">—</Typography.Text>
                    : <Tag color="purple">{embDim} {t('embed.dimensionUnit')}</Tag>
                }
              </Descriptions.Item>
              {metaEntries.length > 0 && metaEntries.map(([k, v]) => (
                <Descriptions.Item key={k} label={<Typography.Text code style={{ fontSize: 12 }}>{k}</Typography.Text>}>
                  <Typography.Text style={{ fontFamily: 'monospace', fontSize: 12 }}>{String(v)}</Typography.Text>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        )
      }
    </div>
  )
}
