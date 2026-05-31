import { Button, Empty, Space, Table, Tag, Typography, Spin, message } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { fetchPayments } from '../api/endpoints'
import PaymentForm from '../components/PaymentForm'
import type { Payment } from '../types'

const methodColors: Record<string, string> = {
  transferencia: 'blue',
  tarjeta: 'cyan',
  efectivo: 'green',
  domiciliacion: 'purple',
}

const emptyText = () => <Empty description="No hay pagos" />

export default function Payments() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Payment | null>(null)

  const load = () => {
    setLoading(true)
    fetchPayments().then(setPayments).catch(() => message.error('Error al cargar pagos')).finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchPayments().then(setPayments).catch(() => message.error('Error al cargar pagos')).finally(() => setLoading(false))
  }, [])

  const columns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Factura', dataIndex: 'invoice_id', key: 'invoice_id' },
    {
      title: 'Importe',
      dataIndex: 'amount',
      key: 'amount',
      render: (v: string) => `${parseFloat(v).toFixed(2)} €`,
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
        <Table rowKey="id" columns={columns} dataSource={payments} pagination={false} locale={{ emptyText }} />
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
