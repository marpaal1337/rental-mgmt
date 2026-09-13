import { PercentageOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import {
  Card, Col, Descriptions, Empty, Row, Select, Space, Spin, Statistic, Table, Tabs, Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo, useState } from 'react'
import { fetchIncomeReport, fetchVatReport, fetchWithholdingsReport } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import type { FiscalIncomeRow, FiscalVatRow, FiscalWithholdingRow } from '../types'
import { fmtMoney } from '../utils/format'
import { expenseCategoryLabels } from '../utils/labels'

const QUARTERS = [
  { label: '1T', value: 1 },
  { label: '2T', value: 2 },
  { label: '3T', value: 3 },
  { label: '4T', value: 4 },
]

const YEARS = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i)

const currentYear = new Date().getFullYear()
const currentQuarter = Math.floor(new Date().getMonth() / 3) + 1

function ResultsCards({ rows }: { rows: { title: string; value: string; color?: string }[] }) {
  return (
    <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
      {rows.map((row) => (
        <Col key={row.title} xs={12} sm={6}>
          <Card>
            <Statistic
              title={row.title}
              value={fmtMoney(row.value)}
              styles={row.color ? { content: { color: row.color } } : undefined}
            />
          </Card>
        </Col>
      ))}
    </Row>
  )
}

function VatTab({ year, quarter, onQuarterChange }: {
  year: number
  quarter: number
  onQuarterChange: (quarter: number) => void
}) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.fiscalVat(year, quarter),
    queryFn: () => fetchVatReport(year, quarter),
  })

  const columns = useMemo<ColumnsType<FiscalVatRow>>(
    () => [
      { title: 'Tipo', dataIndex: 'vat_rate', key: 'vat_rate', render: (value: string) => `${value} %` },
      { title: 'Base imponible', dataIndex: 'base', key: 'base', render: (value: string) => fmtMoney(value) },
      { title: 'Cuota', dataIndex: 'vat', key: 'vat', render: (value: string) => fmtMoney(value) },
    ],
    [],
  )

  if (isError) {
    return <Typography.Text type="danger">Error al cargar el informe: {(error as Error).message}</Typography.Text>
  }

  const totals = data?.totals
  const vatDue = totals ? parseFloat(totals.vat_due) : 0
  const hasOperations = data
    ? data.output.length > 0 || data.input.length > 0 || parseFloat(data.totals.exempt_base) !== 0
    : false

  return (
    <Spin spinning={isLoading}>
      <Space style={{ marginBottom: 16 }}>
        <Typography.Text>Trimestre:</Typography.Text>
        <Select value={quarter} onChange={onQuarterChange} options={QUARTERS} style={{ width: 100 }} />
        <Typography.Text type="secondary">{data?.date_from} — {data?.date_to}</Typography.Text>
      </Space>
      {totals && (
        <ResultsCards
          rows={[
            { title: 'IVA devengado', value: totals.output_vat },
            { title: 'IVA soportado', value: totals.input_vat },
            { title: 'Resultado', value: totals.vat_due, color: vatDue < 0 ? '#cf1322' : '#3f8600' },
            { title: 'Operaciones exentas', value: totals.exempt_base },
          ]}
        />
      )}
      {data && !hasOperations ? (
        <Empty description="Sin operaciones en el trimestre" style={{ margin: '40px 0' }} />
      ) : (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="IVA repercutido" size="small">
              <Table rowKey="vat_rate" columns={columns} dataSource={data?.output ?? []} pagination={false} size="small" />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="IVA soportado deducible" size="small">
              <Table rowKey="vat_rate" columns={columns} dataSource={data?.input ?? []} pagination={false} size="small" />
            </Card>
          </Col>
        </Row>
      )}
      {data && (
        <Typography.Text type="secondary" style={{ display: 'block', marginTop: 12, fontSize: 12 }}>
          {data.criteria}. Las facturas rectificativas se computan en el trimestre en que se emiten.
        </Typography.Text>
      )}
    </Spin>
  )
}

function WithholdingsTab({ year }: { year: number }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.fiscalWithholdings(year),
    queryFn: () => fetchWithholdingsReport(year),
  })

  const columns = useMemo<ColumnsType<FiscalWithholdingRow>>(
    () => [
      { title: 'Inquilino', dataIndex: 'recipient_name', key: 'recipient_name' },
      {
        title: 'NIF',
        key: 'document',
        render: (_: unknown, record: FiscalWithholdingRow) =>
          record.recipient_document_number
            ? `${record.recipient_document_type ?? ''} ${record.recipient_document_number}`.trim()
            : '-',
      },
      { title: 'Facturas', dataIndex: 'invoice_count', key: 'invoice_count', width: 90 },
      { title: 'Base', dataIndex: 'base', key: 'base', render: (value: string) => fmtMoney(value) },
      {
        title: 'Retención',
        dataIndex: 'withholding',
        key: 'withholding',
        render: (value: string) => fmtMoney(value),
      },
    ],
    [],
  )

  if (isError) {
    return <Typography.Text type="danger">Error al cargar el informe: {(error as Error).message}</Typography.Text>
  }

  return (
    <Spin spinning={isLoading}>
      {data && (
        <ResultsCards
          rows={[
            { title: 'Base total', value: data.totals.base },
            { title: 'Retenciones practicadas', value: data.totals.withholding },
          ]}
        />
      )}
      <Table
        rowKey="recipient_document_number"
        columns={columns}
        dataSource={data?.rows ?? []}
        pagination={false}
        locale={{ emptyText: <Empty description="Sin retenciones en el ejercicio" /> }}
      />
      {data && (
        <Typography.Text type="secondary" style={{ display: 'block', marginTop: 12, fontSize: 12 }}>
          {data.criteria}. Resumen orientativo de las retenciones que tus inquilinos han ingresado
          a cuenta de tu IRPF; contrasta con el modelo 190 presentado por cada inquilino.
        </Typography.Text>
      )}
    </Spin>
  )
}

function IncomeTab({ year }: { year: number }) {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.fiscalIncome(year),
    queryFn: () => fetchIncomeReport(year),
  })

  const columns = useMemo<ColumnsType<FiscalIncomeRow>>(
    () => [
      { title: 'Propiedad', dataIndex: 'property_name', key: 'property_name' },
      { title: 'Propietario', dataIndex: 'owner_name', key: 'owner_name' },
      { title: 'Facturas', dataIndex: 'invoice_count', key: 'invoice_count', width: 90 },
      {
        title: 'Ingresos',
        dataIndex: 'gross_income',
        key: 'gross_income',
        render: (value: string) => fmtMoney(value),
      },
      {
        title: 'Gastos deducibles',
        dataIndex: 'deductible_expenses',
        key: 'deductible_expenses',
        render: (value: string) => fmtMoney(value),
      },
      {
        title: 'No deducibles',
        dataIndex: 'non_deductible_expenses',
        key: 'non_deductible_expenses',
        render: (value: string) => fmtMoney(value),
      },
      {
        title: 'Rendimiento neto',
        dataIndex: 'net_income',
        key: 'net_income',
        render: (value: string) => (
          <span style={{ color: parseFloat(value) >= 0 ? '#3f8600' : '#cf1322' }}>{fmtMoney(value)}</span>
        ),
      },
    ],
    [],
  )

  if (isError) {
    return <Typography.Text type="danger">Error al cargar el informe: {(error as Error).message}</Typography.Text>
  }

  return (
    <Spin spinning={isLoading}>
      {data && (
        <ResultsCards
          rows={[
            { title: 'Ingresos', value: data.totals.gross_income },
            { title: 'Gastos deducibles', value: data.totals.deductible_expenses },
            { title: 'Gastos no deducibles', value: data.totals.non_deductible_expenses },
            { title: 'Rendimiento neto', value: data.totals.net_income },
          ]}
        />
      )}
      <Table
        rowKey="property_id"
        columns={columns}
        dataSource={data?.rows ?? []}
        pagination={false}
        locale={{ emptyText: <Empty description="Sin actividad en el ejercicio" /> }}
        expandable={{
          rowExpandable: (record: FiscalIncomeRow) => Object.keys(record.by_category).length > 0,
          expandedRowRender: (record: FiscalIncomeRow) => (
            <Descriptions size="small" column={3} bordered>
              {Object.entries(record.by_category).map(([category, amount]) => (
                <Descriptions.Item key={category} label={expenseCategoryLabels[category] ?? category}>
                  {fmtMoney(amount)}
                </Descriptions.Item>
              ))}
            </Descriptions>
          ),
        }}
      />
      {data && (
        <Typography.Text type="secondary" style={{ display: 'block', marginTop: 12, fontSize: 12 }}>
          {data.criteria}. Ingresos declarables sin IVA. Los gastos no deducibles no minoran el
          rendimiento neto.
        </Typography.Text>
      )}
    </Spin>
  )
}

export default function Fiscal() {
  const [year, setYear] = useState(currentYear)
  const [quarter, setQuarter] = useState(currentQuarter)

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          <PercentageOutlined />
          Informes Fiscales
        </Space>
      </Typography.Title>
      <Space style={{ marginBottom: 16 }}>
        <Typography.Text>Ejercicio:</Typography.Text>
        <Select
          value={year}
          onChange={setYear}
          options={YEARS.map((value) => ({ label: String(value), value }))}
          style={{ width: 100 }}
        />
      </Space>
      <Tabs
        items={[
          {
            key: 'vat',
            label: 'IVA (303)',
            children: <VatTab year={year} quarter={quarter} onQuarterChange={setQuarter} />,
          },
          {
            key: 'withholdings',
            label: 'Retenciones (190)',
            children: <WithholdingsTab year={year} />,
          },
          {
            key: 'income',
            label: 'Renta (100)',
            children: <IncomeTab year={year} />,
          },
        ]}
      />
    </>
  )
}
