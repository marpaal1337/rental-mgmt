import { Button, Descriptions, Empty, Modal, Space, Table, Tag, Typography, Spin, message } from 'antd'
import { DownloadOutlined, PlusOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { downloadInvoicePdf, fetchInvoice, fetchInvoices } from '../api/endpoints'
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

const emptyText = () => <Empty description="No hay facturas" />

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [detailInvoice, setDetailInvoice] = useState<Invoice | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const load = () => {
    setLoading(true)
    fetchInvoices().then(setInvoices).catch(() => message.error('Error al cargar facturas')).finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchInvoices().then(setInvoices).catch(() => message.error('Error al cargar facturas')).finally(() => setLoading(false))
  }, [])

  const openDetail = useCallback(async (invoiceId: number) => {
    setDetailLoading(true)
    try {
      const inv = await fetchInvoice(invoiceId)
      setDetailInvoice(inv)
    } catch {
      message.error('Error al cargar detalle')
    } finally {
      setDetailLoading(false)
    }
  }, [])

  const columns = useMemo(() => [
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
          aria-label="Descargar PDF"
          onClick={(e) => { e.stopPropagation(); downloadInvoicePdf(r.id).catch(() => message.error('Error al descargar PDF')) }}
        >
          PDF
        </Button>
      ),
    },
  ], [])

  const lineColumns = useMemo(() => [
    { title: 'Concepto', dataIndex: 'concept', key: 'concept' },
    { title: 'Base', dataIndex: 'base_amount', key: 'base_amount', render: (v: string) => `${parseFloat(v).toFixed(2)} €` },
    { title: 'IVA %', dataIndex: 'vat_rate', key: 'vat_rate', render: (v: string) => `${parseFloat(v).toFixed(2)}%` },
    { title: 'IVA', dataIndex: 'vat_amount', key: 'vat_amount', render: (v: string) => `${parseFloat(v).toFixed(2)} €` },
    { title: 'IRPF %', dataIndex: 'irpf_rate', key: 'irpf_rate', render: (v: string) => `${parseFloat(v).toFixed(2)}%` },
    { title: 'Ret. IRPF', dataIndex: 'irpf_withholding', key: 'irpf_withholding', render: (v: string) => `${parseFloat(v).toFixed(2)} €` },
  ], [])

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Facturas
          <Button type="primary" icon={<PlusOutlined />} aria-label="Generar facturas" onClick={() => setFormOpen(true)}>
            Generar
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={invoices}
          pagination={false}
          locale={{ emptyText }}
          onRow={(r) => ({ onClick: () => openDetail(r.id), style: { cursor: 'pointer' } })}
        />
      </Spin>
      <InvoiceGenerateForm open={formOpen} onClose={() => setFormOpen(false)} onGenerated={load} />
      <Modal
        title={`Factura #${detailInvoice?.id}`}
        open={!!detailInvoice}
        onCancel={() => setDetailInvoice(null)}
        footer={null}
        width={700}
        loading={detailLoading}
      >
        {detailInvoice && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Periodo">{detailInvoice.period}</Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag color={statusColors[detailInvoice.status] ?? 'default'}>{statusLabels[detailInvoice.status] ?? detailInvoice.status}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Emisión">{detailInvoice.issue_date}</Descriptions.Item>
              <Descriptions.Item label="Total">{parseFloat(detailInvoice.total).toFixed(2)} €</Descriptions.Item>
              {detailInvoice.notes && <Descriptions.Item label="Notas" span={2}>{detailInvoice.notes}</Descriptions.Item>}
            </Descriptions>
            <Typography.Text strong>Líneas</Typography.Text>
            <Table rowKey="id" columns={lineColumns} dataSource={detailInvoice.lines ?? []} pagination={false} size="small" style={{ marginTop: 8 }} />
          </>
        )}
      </Modal>
    </>
  )
}
