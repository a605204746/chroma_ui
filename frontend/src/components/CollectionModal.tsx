import { useEffect, useState } from 'react'
import { Modal, Form, Input, Button, Space, message } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import type { Collection } from '../types'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'

interface Props {
  open: boolean
  editCollection?: Collection | null
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

export default function CollectionModal({ open, editCollection, onClose, onSaved }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [metaRows, setMetaRows] = useState<MetaRow[]>([])
  const { activeConnId, setCollections } = useAppStore()
  const { t } = useTranslation()
  const isEdit = !!editCollection

  useEffect(() => {
    if (open && editCollection) {
      form.setFieldsValue({ name: editCollection.name })
      setMetaRows(objToRows(editCollection.metadata ?? {}))
    } else if (open && !editCollection) {
      form.resetFields()
      setMetaRows([])
    }
  }, [open, editCollection])

  const addRow = () => setMetaRows(r => [...r, { key: '', value: '' }])
  const updateRow = (i: number, field: 'key' | 'value', val: string) =>
    setMetaRows(r => r.map((row, idx) => idx === i ? { ...row, [field]: val } : row))
  const removeRow = (i: number) => setMetaRows(r => r.filter((_, idx) => idx !== i))

  const handleClose = () => {
    form.resetFields()
    setMetaRows([])
    onClose()
  }

  const handleSubmit = async () => {
    if (!activeConnId) return
    try {
      const values = await form.validateFields()
      const dupKeys = metaRows.map(r => r.key.trim()).filter(k => k)
      if (dupKeys.length !== new Set(dupKeys).size) {
        message.error(t('collModal.duplicateKey'))
        return
      }
      setLoading(true)
      const metaObj = rowsToObj(metaRows)
      const metaJson = Object.keys(metaObj).length ? JSON.stringify(metaObj) : ''

      let res
      if (isEdit) {
        res = await bridge.modifyCollection(activeConnId, editCollection.name, values.name, metaJson)
      } else {
        res = await bridge.createCollection(activeConnId, values.name, metaJson)
      }

      if (res.error || res.success === false) {
        message.error(res.error || t(isEdit ? 'collModal.editFailed' : 'collModal.createFailed'))
        return
      }

      const cols = await bridge.listCollections(activeConnId)
      setCollections(Array.isArray(cols) ? cols : [])
      message.success(t(isEdit ? 'collModal.editSuccess' : 'collModal.createSuccess', { name: values.name }))
      handleClose()
      onSaved()
    } catch {
      // validation errors
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={t(isEdit ? 'collModal.editTitle' : 'collModal.title')}
      open={open}
      onCancel={handleClose}
      width={520}
      footer={[
        <Button key="cancel" onClick={handleClose}>{t('collModal.cancel')}</Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          {t(isEdit ? 'collModal.save' : 'collModal.create')}
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label={t('collModal.name')}
          rules={[
            { required: true, message: t('collModal.nameRequired') },
            { pattern: /^[a-zA-Z0-9_-]+$/, message: t('collModal.namePattern') },
          ]}
        >
          <Input placeholder={t('collModal.placeholder')} />
        </Form.Item>
      </Form>

      <div style={{ marginBottom: 6, fontWeight: 500, fontSize: 14 }}>{t('collModal.metadata')}</div>
      <div style={{ marginBottom: 4 }}>
        {metaRows.map((row, i) => (
          <Space key={i} style={{ display: 'flex', marginBottom: 6 }} align="center">
            <Input
              placeholder="key"
              value={row.key}
              onChange={e => updateRow(i, 'key', e.target.value)}
              style={{ width: 160, fontFamily: 'monospace' }}
            />
            <Input
              placeholder="value"
              value={row.value}
              onChange={e => updateRow(i, 'value', e.target.value)}
              style={{ width: 220 }}
            />
            <Button type="text" danger icon={<DeleteOutlined />} onClick={() => removeRow(i)} />
          </Space>
        ))}
        <Button type="dashed" icon={<PlusOutlined />} onClick={addRow} block style={{ marginTop: 4 }}>
          {t('collModal.addField')}
        </Button>
      </div>
    </Modal>
  )
}
