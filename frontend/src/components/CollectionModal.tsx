import { useState } from 'react'
import { Modal, Form, Input, Button, message } from 'antd'
import { useTranslation } from 'react-i18next'
import { bridge } from '../api/bridge'
import { useAppStore } from '../store/appStore'

interface Props {
  open: boolean
  onClose: () => void
}

export default function CollectionModal({ open, onClose }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const { activeConnId, setCollections } = useAppStore()
  const { t } = useTranslation()

  const handleSubmit = async () => {
    if (!activeConnId) return
    try {
      const values = await form.validateFields()
      setLoading(true)
      const res = await bridge.createCollection(activeConnId, values.name)
      if (res.error || res.success === false) {
        message.error(res.error || t('collModal.createFailed'))
        return
      }
      const cols = await bridge.listCollections(activeConnId)
      setCollections(Array.isArray(cols) ? cols : [])
      message.success(t('collModal.createSuccess', { name: values.name }))
      form.resetFields()
      onClose()
    } catch {
      // validation errors
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={t('collModal.title')}
      open={open}
      onCancel={() => { form.resetFields(); onClose() }}
      footer={[
        <Button key="cancel" onClick={() => { form.resetFields(); onClose() }}>{t('collModal.cancel')}</Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>{t('collModal.create')}</Button>,
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
    </Modal>
  )
}
