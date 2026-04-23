import { Button, Input, Select, Space } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useTranslation } from 'react-i18next'

export interface FilterRow {
  key: string
  op: string
  value: string
}

interface Props {
  rows: FilterRow[]
  onChange: (rows: FilterRow[]) => void
}

export function buildWhereJson(rows: FilterRow[]): string {
  if (rows.length === 0) return ''
  const conditions: Record<string, unknown>[] = rows
    .filter(r => r.key && r.value)
    .map(r => {
      let val: unknown = r.value
      if (r.op === '$in') {
        val = r.value.split(',').map(s => s.trim())
      } else if (!isNaN(Number(r.value))) {
        val = Number(r.value)
      }
      return { [r.key]: { [r.op]: val } }
    })
  if (conditions.length === 0) return ''
  if (conditions.length === 1) return JSON.stringify(conditions[0])
  return JSON.stringify({ $and: conditions })
}

export default function FilterBuilder({ rows, onChange }: Props) {
  const { t } = useTranslation()

  const OPS = [
    { value: '$eq', label: t('filter.eq') },
    { value: '$ne', label: t('filter.ne') },
    { value: '$gt', label: t('filter.gt') },
    { value: '$gte', label: t('filter.gte') },
    { value: '$lt', label: t('filter.lt') },
    { value: '$lte', label: t('filter.lte') },
    { value: '$in', label: t('filter.in') },
  ]

  const addRow = () => onChange([...rows, { key: '', op: '$eq', value: '' }])
  const removeRow = (i: number) => onChange(rows.filter((_, idx) => idx !== i))
  const updateRow = (i: number, field: keyof FilterRow, val: string) =>
    onChange(rows.map((r, idx) => idx === i ? { ...r, [field]: val } : r))

  return (
    <div>
      {rows.map((row, i) => (
        <Space key={i} style={{ display: 'flex', marginBottom: 6 }}>
          <Input
            placeholder={t('filter.fieldPlaceholder')}
            value={row.key}
            onChange={e => updateRow(i, 'key', e.target.value)}
            style={{ width: 130 }}
          />
          <Select
            value={row.op}
            onChange={v => updateRow(i, 'op', v)}
            options={OPS}
            style={{ width: 120 }}
          />
          <Input
            placeholder={row.op === '$in' ? t('filter.inValuePlaceholder') : t('filter.valuePlaceholder')}
            value={row.value}
            onChange={e => updateRow(i, 'value', e.target.value)}
            style={{ width: 160 }}
          />
          <Button type="text" danger icon={<DeleteOutlined />} onClick={() => removeRow(i)} />
        </Space>
      ))}
      <Button type="dashed" icon={<PlusOutlined />} onClick={addRow} size="small">
        {t('filter.addCondition')}
      </Button>
    </div>
  )
}
