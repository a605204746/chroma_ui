import { useEffect, useState } from 'react'
import { Modal, Form, Input, Button, Space, message } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import type { Document } from '../types'
import { documentApi } from '../api'
import { useAppStore } from '../store/appStore'

interface Props {
  open: boolean
  doc: Document | null
  onClose: () => void
  onSaved: () => void
}

interface MetaRow { key: string; value: string }

const objToRows = (obj: Record<string, unknown>): MetaRow[] =>
  Object.entries(obj).map(([k, v]) => ({ key: k, value: String(v) }))

const rowsToObj = (rows: MetaRow[]): Record<string, string> => {
  const result: Record<string, string> = {}
  for (const r of rows) {
    if (r.key.trim()) result[r.key.trim()] = r.value
  }
  return result
}

export default function DocumentModal({ open, doc, onClose, onSaved }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [metaRows, setMetaRows] = useState<MetaRow[]>([])
  const { activeConnId, activeCollection } = useAppStore()
  const { t } = useTranslation()
  const isEdit = !!doc

  useEffect(() => {
    if (open && doc) {
      form.setFieldsValue({ id: doc.id, document: doc.document })
      setMetaRows(objToRows(doc.metadata ?? {}))
    } else if (open && !doc) {
      form.resetFields()
      setMetaRows([])
    }
  }, [open, doc])

  const addRow = () => setMetaRows(r => [...r, { key: '', value: '' }])

  const updateRow = (i: number, field: 'key' | 'value', val: string) =>
    setMetaRows(r => r.map((row, idx) => idx === i ? { ...row, [field]: val } : row))

  const removeRow = (i: number) =>
    setMetaRows(r => r.filter((_, idx) => idx !== i))

  const handleSubmit = async () => {
    if (!activeConnId || !activeCollection) return
    try {
      const values = await form.validateFields()
      const dupKeys = metaRows.map(r => r.key.trim()).filter(k => k)
      if (dupKeys.length !== new Set(dupKeys).size) {
        message.error(t('doc.duplicateKey'))
        return
      }
      setLoading(true)
      const metaObj = rowsToObj(metaRows)
      const metaStr = Object.keys(metaObj).length ? JSON.stringify(metaObj) : ''
      let res
      if (isEdit) {
        res = await documentApi.updateDocument(activeConnId, activeCollection, values.id, values.document, metaStr)
      } else {
        res = await documentApi.addDocument(activeConnId, activeCollection, values.id, values.document, metaStr)
      }
      if (res.error || res.success === false) {
        message.error(res.error || t('doc.failed'))
        return
      }
      message.success(isEdit ? t('doc.updateSuccess') : t('doc.addSuccess'))
      onSaved()
      onClose()
    } catch {
      // validation
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? t('doc.editTitle') : t('doc.addTitle')}
      open={open}
      centered
      width={600}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>{t('doc.cancel')}</Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {isEdit ? t('doc.save') : t('doc.add')}
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="id" label={t('doc.id')} rules={[{ required: true, message: t('doc.id') }]}>
          <Input disabled={isEdit} placeholder={t('doc.idPlaceholder')} />
        </Form.Item>
        <Form.Item name="document" label={t('doc.document')} rules={[{ required: true, message: t('doc.document') }]}>
          <Input.TextArea rows={4} placeholder={t('doc.contentPlaceholder')} />
        </Form.Item>
      </Form>

      <div style={{ marginBottom: 4, fontWeight: 500, fontSize: 14 }}>{t('doc.metadata')}</div>
      <div style={{ marginBottom: 8 }}>
        {metaRows.map((row, i) => (
          <Space key={i} style={{ display: 'flex', marginBottom: 6 }} align="center">
            <Input
              placeholder={t('doc.keyPlaceholder')}
              value={row.key}
              onChange={e => updateRow(i, 'key', e.target.value)}
              style={{ width: 180, fontFamily: 'monospace' }}
            />
            <Input
              placeholder={t('doc.valuePlaceholder')}
              value={row.value}
              onChange={e => updateRow(i, 'value', e.target.value)}
              style={{ width: 240 }}
            />
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => removeRow(i)}
            />
          </Space>
        ))}
        <Button
          type="dashed"
          icon={<PlusOutlined />}
          onClick={addRow}
          block
          style={{ marginTop: 4 }}
        >
          {t('doc.addField')}
        </Button>
      </div>
    </Modal>
  )
}
