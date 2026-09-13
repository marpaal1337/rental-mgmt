import { DownloadOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Descriptions, Empty, Modal, Space, Spin, Table, Tag, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo, useState } from 'react'
import { downloadInvoicePdf, fetchInvoice, fetchInvoices } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import InvoiceGenerateForm from '../components/InvoiceGenerateForm'
import type { Invoice, InvoiceLine } from '../types'
import { fmtMoney } from '../utils/format'
import { invoiceStatusColors, invoiceStatusLabels } from '../utils/labels'

const emptyText = () => <Empty description="No hay facturas" />

export default function Invoices() {
  const [generateOpen, setGenerateOpen] = useState(false)
  const [detailId, setDetailId] = useState<number | null>(null)
  const queryClient = useQueryClient()

  const invoicesQuery = useQuery({
    queryKey: queryKeys.invoices,
    queryFn: fetchInvoices,
  })

  const detailQuery = useQuery({
    queryKey: queryKeys.invoice(detailId ?? 0),
    queryFn: () => fetchInvoice(detailId as number),
    enabled: detailId !== null,
  })

  const columns = useMemo<ColumnsType<Invoice>>(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
      { title: 'Periodo', dataIndex: 'period', key: 'period' },
      {
        title: 'Total',
        dataIndex: 'total',
        key: 'total',
        render: (value: string) => fmtMoney(value),
      },
      {
        title: 'Estado',
        dataIndex: 'status',
        key: 'status',
        render: (value: string) => (
          <Tag color={invoiceStatusColors[value] ?? 'default'}>
            {invoiceStatusLabels[value] ?? value}
          </Tag>
        ),
      },
      { title: 'Emisión', dataIndex: 'issue_date', key: 'issue_date' },
      {
        title: 'PDF',
        key: 'pdf',
        render: (_: unknown, record: Invoice) => (
          <Button
            type="link"
            icon={<DownloadOutlined />}
            aria-label="Descargar PDF"
            onClick={(event) => {
              event.stopPropagation()
              downloadInvoicePdf(record.id).catch((err: Error) => message.error(err.message))
            }}
          >
            PDF
          </Button>
        ),
      },
    ],
    [],
  )

  const lineColumns = useMemo<ColumnsType<InvoiceLine>>(
    () => [
      { title: 'Concepto', dataIndex: 'concept', key: 'concept' },
      { title: 'Base', dataIndex: 'base_amount', key: 'base_amount', render: (v: string) => fmtMoney(v) },
      { title: 'IVA %', dataIndex: 'vat_rate', key: 'vat_rate', render: (v: string) => `${parseFloat(v).toFixed(2)}%` },
      { title: 'IVA', dataIndex: 'vat_amount', key: 'vat_amount', render: (v: string) => fmtMoney(v) },
      { title: 'IRPF %', dataIndex: 'irpf_rate', key: 'irpf_rate', render: (v: string) => `${parseFloat(v).toFixed(2)}%` },
      { title: 'Ret. IRPF', dataIndex: 'irpf_withholding', key: 'irpf_withholding', render: (v: string) => fmtMoney(v) },
    ],
    [],
  )

  const invoice = detailQuery.data

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Facturas
          <Button type="primary" icon={<PlusOutlined />} aria-label="Generar facturas" onClick={() => setGenerateOpen(true)}>
            Generar
          </Button>
        </Space>
      </Typography.Title>
      {invoicesQuery.isError && (
        <Typography.Text type="danger" style={{ display: 'block', marginBottom: 12 }}>
          Error al cargar facturas: {(invoicesQuery.error as Error).message}
        </Typography.Text>
      )}
      <Spin spinning={invoicesQuery.isLoading}>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={invoicesQuery.data ?? []}
          pagination={false}
          locale={{ emptyText }}
          onRow={(record) => ({ onClick: () => setDetailId(record.id), style: { cursor: 'pointer' } })}
        />
      </Spin>
      <InvoiceGenerateForm
        open={generateOpen}
        onClose={() => setGenerateOpen(false)}
        onGenerated={() => queryClient.invalidateQueries({ queryKey: queryKeys.invoices })}
      />
      <Modal
        title={`Factura #${detailId ?? ''}`}
        open={detailId !== null}
        onCancel={() => setDetailId(null)}
        footer={null}
        width={700}
        loading={detailQuery.isLoading}
      >
        {invoice && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Periodo">{invoice.period}</Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag color={invoiceStatusColors[invoice.status] ?? 'default'}>
                  {invoiceStatusLabels[invoice.status] ?? invoice.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Emisión">{invoice.issue_date}</Descriptions.Item>
              <Descriptions.Item label="Total">{fmtMoney(invoice.total)}</Descriptions.Item>
              {invoice.notes && <Descriptions.Item label="Notas" span={2}>{invoice.notes}</Descriptions.Item>}
            </Descriptions>
            <Typography.Text strong>Líneas</Typography.Text>
            <Table rowKey="id" columns={lineColumns} dataSource={invoice.lines ?? []} pagination={false} size="small" style={{ marginTop: 8 }} />
          </>
        )}
      </Modal>
    </>
  )
}
