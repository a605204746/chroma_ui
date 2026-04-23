import { DatabaseOutlined, PlusOutlined } from '@ant-design/icons'
import { Button, Typography } from 'antd'

interface Props {
  onAddConnection: () => void
}

export default function WelcomePage({ onAddConnection }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 16 }}>
      <DatabaseOutlined style={{ fontSize: 64, color: '#8b5cf6' }} />
      <Typography.Title level={3} style={{ margin: 0 }}>欢迎使用 Chroma UI</Typography.Title>
      <Typography.Text type="secondary">添加一个连接以开始浏览 ChromaDB 数据</Typography.Text>
      <Button type="primary" icon={<PlusOutlined />} size="large" onClick={onAddConnection}>
        新增连接
      </Button>
    </div>
  )
}
