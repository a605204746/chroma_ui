import { useEffect, useState } from 'react'
import { Modal, Form, Input, InputNumber, Button, message, Radio, Space, Typography } from 'antd'
import { FolderOpenOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'
import { connectionApi } from '../api'
import { useAppStore } from '../store/appStore'
import type { Connection } from '../types'

interface Props {
  open: boolean
  editingConn?: Connection | null
  onClose: () => void
}

export default function ConnectionModal({ open, editingConn, onClose }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [picking, setPicking] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; error?: string } | null>(null)
  const { setConnections } = useAppStore()
  const { t } = useTranslation()
  const connType = Form.useWatch('conn_type', form)
  const isEdit = !!editingConn

  useEffect(() => {
    if (open && editingConn) {
      form.setFieldsValue({
        name: editingConn.name,
        conn_type: editingConn.conn_type,
        host: editingConn.host,
        port: editingConn.port,
        path: editingConn.path,
        token: editingConn.token ?? '',
      })
    } else if (open && !editingConn) {
      form.resetFields()
    }
    setTestResult(null)
  }, [open, editingConn])

  const handlePickDir = async () => {
    setPicking(true)
    try {
      const dir = await connectionApi.pickDirectory()
      if (dir) form.setFieldValue('path', dir)
    } finally {
      setPicking(false)
    }
  }

  const handleTest = async () => {
    try {
      const values = await form.validateFields(
        connType === 'persistent' ? ['path'] : ['host', 'port']
      )
      setTesting(true)
      setTestResult(null)
      const res = await connectionApi.testConnection(
        connType ?? 'persistent',
        values.host ?? form.getFieldValue('host') ?? '',
        values.port ?? form.getFieldValue('port') ?? 8000,
        values.path ?? form.getFieldValue('path') ?? '',
        connType === 'http' ? (form.getFieldValue('token') ?? '') : '',
      )
      setTestResult(res)
    } catch {
      // validation
    } finally {
      setTesting(false)
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const token = values.conn_type === 'http' ? (values.token ?? '') : ''
      if (isEdit) {
        await connectionApi.updateConnection(editingConn.id, values.name, values.conn_type,
          values.host ?? '', values.port ?? 8000, true, values.path ?? '', token)
      } else {
        await connectionApi.addConnection(values.name, values.conn_type,
          values.host ?? '', values.port ?? 8000, true, values.path ?? '', token)
      }
      const conns = await connectionApi.getConnections()
      setConnections(conns)
      message.success(isEdit ? t('connModal.updated') : t('connModal.added'))
      form.resetFields()
      onClose()
    } catch {
      // antd validation
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => { form.resetFields(); setTestResult(null); onClose() }

  return (
    <Modal
      title={isEdit ? t('connModal.editTitle') : t('connModal.addTitle')}
      open={open}
      centered
      onCancel={handleClose}
      footer={[
        <Button key="cancel" onClick={handleClose}>{t('connModal.cancel')}</Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>{t('connModal.save')}</Button>,
      ]}
    >
      <Form form={form} layout="vertical"
        initialValues={{ conn_type: 'persistent', host: 'localhost', port: 8000, path: '' }}>
        <Form.Item name="name" label={t('connModal.name')} rules={[{ required: true, message: t('connModal.nameRequired') }]}>
          <Input placeholder={t('connModal.namePlaceholder')} />
        </Form.Item>
        <Form.Item name="conn_type" label={t('connModal.type')}>
          <Radio.Group onChange={() => setTestResult(null)}>
            <Radio value="persistent">{t('connModal.persistType')}</Radio>
            <Radio value="http">{t('connModal.httpType')}</Radio>
          </Radio.Group>
        </Form.Item>
        {connType === 'persistent' ? (
          <Form.Item name="path" label={t('connModal.path')} rules={[{ required: true, message: t('connModal.pathRequired') }]}>
            <Input placeholder={t('connModal.pathPlaceholder')} readOnly
              addonAfter={
                <Button type="text" size="small" icon={<FolderOpenOutlined />}
                  loading={picking} onClick={handlePickDir}
                  style={{ height: '100%', border: 'none' }}>{t('connModal.browse')}</Button>
              }
            />
          </Form.Item>
        ) : (
          <>
            <Form.Item name="host" label={t('connModal.host')} rules={[{ required: true, message: t('connModal.hostRequired') }]}>
              <Input placeholder="localhost" onChange={() => setTestResult(null)} />
            </Form.Item>
            <Form.Item name="port" label={t('connModal.port')} rules={[{ required: true, message: t('connModal.portRequired') }]}>
              <InputNumber min={1} max={65535} style={{ width: '100%' }} onChange={() => setTestResult(null)} />
            </Form.Item>
            <Form.Item name="token" label={t('connModal.token')}>
              <Input.Password placeholder={t('connModal.tokenPlaceholder')} autoComplete="off" onChange={() => setTestResult(null)} />
            </Form.Item>
          </>
        )}

        <Space align="center">
          <Button loading={testing} onClick={handleTest}>{t('connModal.testBtn')}</Button>
          {testResult && (
            testResult.success
              ? <Space size={4}>
                  <CheckCircleOutlined style={{ color: '#22c55e' }} />
                  <Typography.Text style={{ color: '#22c55e', fontSize: 13 }}>{t('connModal.testSuccess')}</Typography.Text>
                </Space>
              : <Space size={4}>
                  <CloseCircleOutlined style={{ color: '#ef4444' }} />
                  <Typography.Text type="danger" style={{ fontSize: 13 }}>{t('connModal.testFail')}: {testResult.error}</Typography.Text>
                </Space>
          )}
        </Space>
      </Form>
    </Modal>
  )
}
