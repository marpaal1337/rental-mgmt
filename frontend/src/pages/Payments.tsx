import { Button, Empty, Space, Table, Tag, Typography, Spin } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useMemo, useState } from 'react'
import { fetchPayments } from '../api/endpoints'
import PaymentForm from '../components/PaymentForm'
import { useFetch } from '../hooks/useFetch'
import type { Payment } from '../types'
import { fmtMoney } from '../utils/format'

const methodColors: Record<string, string> = {
  transferencia: 'blue',
  tarjeta: 'cyan',
  efectivo: 'green',
  domiciliacion: 'purple',
}

const emptyText = () => <Empty description="No hay pagos" />

export default function Payments() {
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Payment | null>(null)
  const { data: payments, loading, load } = useFetch(() => fetchPayments())

  const columns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Factura', dataIndex: 'invoice_id', key: 'invoice_id' },
    {
      title: 'Importe',
      dataIndex: 'amount',
      key: 'amount',
      render: (v: string) => fmtMoney(v),
    },
    { title: 'Fecha', dataIndex: 'payment_date', key: 'payment_date' },
    {
      title: 'Método',
      dataIndex: 'method',
      key: 'method',
      render: (v: string) => (
        <Tag color={methodColors[v] ?? 'default'}>{v}</Tag>
      ),
    },
    {
      title: 'Notas',
      dataIndex: 'notes',
      key: 'notes',
      render: (v: string | null) => v ?? '-',
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: Payment) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          aria-label="Editar pago"
          onClick={() => {
            setEditing(r)
            setFormOpen(true)
          }}
        />
      ),
    },
  ], [])

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Pagos
          <Button type="primary" icon={<PlusOutlined />} aria-label="Registrar pago" onClick={() => { setEditing(null); setFormOpen(true) }}>
            Registrar
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={payments ?? []} pagination={false} locale={{ emptyText }} />
      </Spin>
      <PaymentForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={load}
        payment={editing}
      />
    </>
  )
}
