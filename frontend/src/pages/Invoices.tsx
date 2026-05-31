import { Button, Space, Table, Tag, Typography, Spin, message } from 'antd'
import { DownloadOutlined, PlusOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { fetchInvoicePdfUrl, fetchInvoices } from '../api/endpoints'
import InvoiceGenerateForm from '../components/InvoiceGenerateForm'
import type { Invoice } from '../types'

const statusColors: Record<string, string> = {
  draft: 'default',
  partial: 'orange',
  paid: 'green',
}

const statusLabels: Record<string, string> = {
  draft: 'Borrador',
  partial: 'Parcial',
  paid: 'Pagada',
}

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)

  const load = () => {
    setLoading(true)
    fetchInvoices().then(setInvoices).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Periodo', dataIndex: 'period', key: 'period' },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      render: (v: string) => `${parseFloat(v).toFixed(2)} €`,
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => (
        <Tag color={statusColors[v] ?? 'default'}>{statusLabels[v] ?? v}</Tag>
      ),
    },
    { title: 'Emisión', dataIndex: 'issue_date', key: 'issue_date' },
    {
      title: 'PDF',
      key: 'pdf',
      render: (_: unknown, r: Invoice) => (
        <Button
          type="link"
          icon={<DownloadOutlined />}
          onClick={async () => {
            try {
              const url = await fetchInvoicePdfUrl(r.id)
              window.open(url, '_blank')
            } catch {
              message.error('Error al descargar PDF')
            }
          }}
        >
          PDF
        </Button>
      ),
    },
  ]

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Facturas
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setFormOpen(true)}>
            Generar
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={invoices} pagination={false} />
      </Spin>
      <InvoiceGenerateForm
        open={formOpen}
        onClose={() => setFormOpen(false)}
        onGenerated={load}
      />
    </>
  )
}
