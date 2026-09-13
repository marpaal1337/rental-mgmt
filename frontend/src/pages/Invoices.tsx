import { DownloadOutlined, PlusOutlined, RollbackOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Descriptions, Empty, Input, Modal, Space, Spin, Table, Tag, Typography, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo, useState } from 'react'
import { downloadInvoicePdf, fetchInvoice, fetchInvoices, rectifyInvoice } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import InvoiceGenerateForm from '../components/InvoiceGenerateForm'
import type { Invoice, InvoiceLine } from '../types'
import { fmtMoney } from '../utils/format'
import { invoiceStatusColors, invoiceStatusLabels } from '../utils/labels'

const emptyText = () => <Empty description="No hay facturas" />

export default function Invoices() {
  const [generateOpen, setGenerateOpen] = useState(false)
  const [detailId, setDetailId] = useState<number | null>(null)
  const [rectifyOpen, setRectifyOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [rectifying, setRectifying] = useState(false)
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
      {
        title: 'Nº',
        dataIndex: 'number',
        key: 'number',
        render: (value: string | null, record: Invoice) => value ?? `#${record.id}`,
      },
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
        title: 'Vencimiento',
        dataIndex: 'due_date',
        key: 'due_date',
        render: (value: string | null) => value ?? '—',
      },
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

  const handleRectify = async () => {
    if (!invoice || !reason.trim()) {
      return
    }
    setRectifying(true)
    try {
      await rectifyInvoice(invoice.id, { reason: reason.trim() })
      message.success('Factura rectificada')
      setRectifyOpen(false)
      setReason('')
      setDetailId(null)
      queryClient.invalidateQueries({ queryKey: queryKeys.invoices })
      queryClient.invalidateQueries({ queryKey: queryKeys.stats })
    } catch (err) {
      message.error(err instanceof Error ? err.message : 'Error al rectificar la factura')
    } finally {
      setRectifying(false)
    }
  }

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
        title={`Factura ${invoice?.number ?? `#${detailId ?? ''}`}`}
        open={detailId !== null}
        onCancel={() => setDetailId(null)}
        footer={null}
        width={700}
        loading={detailQuery.isLoading}
      >
        {invoice && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Nº">{invoice.number ?? `#${invoice.id}`}</Descriptions.Item>
              <Descriptions.Item label="Periodo">{invoice.period}</Descriptions.Item>
              <Descriptions.Item label="Estado">
                <Tag color={invoiceStatusColors[invoice.status] ?? 'default'}>
                  {invoiceStatusLabels[invoice.status] ?? invoice.status}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Emisión">{invoice.issue_date}</Descriptions.Item>
              <Descriptions.Item label="Vencimiento">{invoice.due_date ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="Total">{fmtMoney(invoice.total)}</Descriptions.Item>
              {invoice.corrected_invoice_id && (
                <Descriptions.Item label="Rectifica a" span={2}>
                  Factura #{invoice.corrected_invoice_id}
                </Descriptions.Item>
              )}
              {invoice.rectification_reason && (
                <Descriptions.Item label="Motivo" span={2}>
                  {invoice.rectification_reason}
                </Descriptions.Item>
              )}
              {invoice.notes && <Descriptions.Item label="Notas" span={2}>{invoice.notes}</Descriptions.Item>}
            </Descriptions>
            <Typography.Text strong>Líneas</Typography.Text>
            <Table rowKey="id" columns={lineColumns} dataSource={invoice.lines ?? []} pagination={false} size="small" style={{ marginTop: 8 }} />
            {!invoice.corrected_invoice_id && (
              <Button
                danger
                icon={<RollbackOutlined />}
                style={{ marginTop: 16 }}
                onClick={() => setRectifyOpen(true)}
              >
                Rectificar
              </Button>
            )}
          </>
        )}
      </Modal>
      <Modal
        title="Rectificar factura"
        open={rectifyOpen}
        onCancel={() => setRectifyOpen(false)}
        onOk={handleRectify}
        confirmLoading={rectifying}
        okText="Crear rectificativa"
        okButtonProps={{ danger: true, disabled: !reason.trim() }}
      >
        <Typography.Paragraph>
          Se creará una factura rectificativa con los importes negados. La factura original
          se mantiene y no podrá rectificarse de nuevo.
        </Typography.Paragraph>
        <Input.TextArea
          rows={3}
          maxLength={500}
          showCount
          placeholder="Motivo de la rectificación"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </Modal>
    </>
  )
}
