import { useEffect, useState } from 'react'
import { Modal, Form, Input, Button, message, Alert, Space, Tag, Typography, Tooltip, InputNumber } from 'antd'
import { ApartmentOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { embeddingApi } from '../api'
import { useAppStore } from '../store/appStore'

interface Props {
  open: boolean
  onClose: () => void
  onSaved?: () => void
}

const PRESETS = [
  { label: 'Ollama', url: 'http://localhost:11434/v1/embeddings', model: 'nomic-embed-text' },
  { label: 'OpenAI', url: 'https://api.openai.com/v1/embeddings', model: 'text-embedding-3-small' },
  { label: 'LM Studio', url: 'http://localhost:1234/v1/embeddings', model: '' },
  { label: 'Qwen', url: 'https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings', model: 'text-embedding-v3' },
]

export default function EmbeddingConfigModal({ open, onClose, onSaved }: Props) {
  const { activeConnId, activeCollection } = useAppStore()
  const { t } = useTranslation()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ dimension?: number; error?: string } | null>(null)

  useEffect(() => {
    if (open && activeConnId && activeCollection) {
      embeddingApi.getCollectionEmbedding(activeConnId, activeCollection).then(cfg => {
        form.setFieldsValue({
          embedding_url: cfg.embedding_url ?? '',
          embedding_model: cfg.embedding_model ?? '',
          embedding_api_key: cfg.embedding_api_key ?? '',
          dimension: cfg.dimension || undefined,
        })
      })
      setTestResult(null)
    }
  }, [open, activeConnId, activeCollection])

  const applyPreset = (p: typeof PRESETS[0]) => {
    form.setFieldsValue({ embedding_url: p.url, embedding_model: p.model })
    setTestResult(null)
  }

  const handleTest = async () => {
    if (!activeConnId || !activeCollection) return
    const values = form.getFieldsValue()
    await embeddingApi.setCollectionEmbedding(activeConnId, activeCollection,
      values.embedding_url ?? '', values.embedding_model ?? '', values.embedding_api_key ?? '')
    setTesting(true)
    setTestResult(null)
    try {
      const res = await embeddingApi.testEmbedding(activeConnId, activeCollection, '测试文本 hello')
      setTestResult(res)
      if (res.dimension) {
        form.setFieldValue('dimension', res.dimension)
      }
    } finally {
      setTesting(false)
    }
  }

  const handleSave = async () => {
    if (!activeConnId || !activeCollection) return
    try {
      const values = await form.validateFields()
      setLoading(true)
      await embeddingApi.setCollectionEmbedding(activeConnId, activeCollection,
        values.embedding_url ?? '', values.embedding_model ?? '',
        values.embedding_api_key ?? '', values.dimension ?? 0)
      message.success(t('embed.savedSuccess'))
      onSaved?.()
      onClose()
    } catch {
      // validation
    } finally {
      setLoading(false)
    }
  }

  const handleClear = async () => {
    if (!activeConnId || !activeCollection) return
    await embeddingApi.clearCollectionEmbedding(activeConnId, activeCollection)
    form.resetFields()
    setTestResult(null)
    message.success(t('embed.cleared'))
    onSaved?.()
    onClose()
  }

  const canSave = testResult != null && !testResult.error

  return (
    <Modal
      title={<Space><ApartmentOutlined /><span>{t('embed.title', { name: activeCollection })}</span></Space>}
      open={open}
      centered
      onCancel={onClose}
      width={520}
      footer={[
        <Button key="clear" danger onClick={handleClear}>{t('embed.clear')}</Button>,
        <Button key="cancel" onClick={onClose}>{t('embed.cancel')}</Button>,
        <Tooltip key="save" title={!canSave ? t('embed.saveFirst') : ''}>
          <Button type="primary" loading={loading} onClick={handleSave} disabled={!canSave}>
            {t('embed.save')}
          </Button>
        </Tooltip>,
      ]}
    >
      <Alert
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
        message={t('embed.warning')}
      />

      <div style={{ marginBottom: 12 }}>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>{t('embed.presets')}</Typography.Text>
        <Space size={6} style={{ marginLeft: 8 }}>
          {PRESETS.map(p => (
            <Tag key={p.label} style={{ cursor: 'pointer' }} onClick={() => applyPreset(p)}>{p.label}</Tag>
          ))}
        </Space>
      </div>

      <Form form={form} layout="vertical">
        <Form.Item name="embedding_url" label={t('embed.apiUrl')} rules={[{ required: true, message: t('embed.urlRequired') }]}>
          <Input placeholder="http://localhost:11434/v1/embeddings" />
        </Form.Item>
        <Form.Item name="embedding_model" label={t('embed.modelName')} rules={[{ required: true, message: t('embed.modelRequired') }]}>
          <Input placeholder="nomic-embed-text" style={{ fontFamily: 'monospace' }} />
        </Form.Item>
        <Form.Item name="embedding_api_key" label={t('embed.apiKey')}>
          <Input.Password placeholder={t('embed.apiKeyPlaceholder')} />
        </Form.Item>
        <Form.Item
          name="dimension"
          label={t('embed.dimension')}
          tooltip={t('embed.dimensionTip')}
          rules={[{ required: true, message: t('embed.dimensionRequired') }]}
        >
          <InputNumber
            min={1}
            style={{ width: '100%' }}
            placeholder={t('embed.dimensionPlaceholder')}
            addonAfter={t('embed.dimensionUnit')}
          />
        </Form.Item>

        <Space>
          <Button icon={<ApartmentOutlined />} loading={testing} onClick={handleTest}>
            {t('embed.testBtn')}
          </Button>
          {testResult && (
            testResult.error
              ? <Typography.Text type="danger" style={{ fontSize: 12 }}>{testResult.error}</Typography.Text>
              : <Space size={4}>
                  <CheckCircleOutlined style={{ color: '#22c55e' }} />
                  <Typography.Text style={{ fontSize: 12, color: '#22c55e' }}>
                    {t('embed.testSuccess', { n: testResult.dimension })}
                  </Typography.Text>
                </Space>
          )}
        </Space>
      </Form>
    </Modal>
  )
}
