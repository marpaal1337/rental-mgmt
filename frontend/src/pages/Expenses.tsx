import { BarChartOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, Col, Collapse, Descriptions, Empty, Row, Select, Space, Spin, Statistic, Table, Tag, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo, useState } from 'react'
import { fetchExpenseSummary, fetchExpenses, fetchProperties } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import ExpenseForm from '../components/ExpenseForm'
import type { Expense } from '../types'
import { fmtMoney } from '../utils/format'
import { expenseCategoryLabels } from '../utils/labels'

const emptyText = () => <Empty description="No hay gastos" />

export default function Expenses() {
  const queryClient = useQueryClient()
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Expense | null>(null)
  const [selectedProperty, setSelectedProperty] = useState<number | null>(null)
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear())
  const [summaryRequested, setSummaryRequested] = useState(false)

  const propertiesQuery = useQuery({
    queryKey: queryKeys.properties,
    queryFn: fetchProperties,
  })
  const properties = propertiesQuery.data ?? []
  const propertyId = selectedProperty ?? properties[0]?.id ?? null

  const expensesQuery = useQuery({
    queryKey: queryKeys.expenses(propertyId ?? undefined, selectedYear),
    queryFn: () => fetchExpenses(propertyId as number, selectedYear),
    enabled: propertyId !== null,
  })

  const summaryQuery = useQuery({
    queryKey: queryKeys.expenseSummary(propertyId ?? 0, selectedYear),
    queryFn: () => fetchExpenseSummary(propertyId as number, selectedYear),
    enabled: summaryRequested && propertyId !== null,
  })
  const summary = summaryQuery.data

  const columns = useMemo<ColumnsType<Expense>>(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
      {
        title: 'Categoría',
        dataIndex: 'category',
        key: 'category',
        render: (value: string) => expenseCategoryLabels[value] ?? value,
      },
      {
        title: 'Importe',
        dataIndex: 'amount',
        key: 'amount',
        render: (value: string) => fmtMoney(value),
      },
      { title: 'Fecha', dataIndex: 'expense_date', key: 'expense_date' },
      {
        title: 'Deducible',
        dataIndex: 'deductible',
        key: 'deductible',
        render: (value: boolean) =>
          value ? <Tag color="green">Sí</Tag> : <Tag color="red">No</Tag>,
      },
      {
        title: 'Proveedor',
        dataIndex: 'supplier',
        key: 'supplier',
        render: (value: string | null) => value ?? '-',
      },
      {
        title: '',
        key: 'actions',
        width: 60,
        render: (_: unknown, record: Expense) => (
          <Button
            type="link"
            icon={<EditOutlined />}
            aria-label="Editar gasto"
            onClick={() => {
              setEditing(record)
              setFormOpen(true)
            }}
          />
        ),
      },
    ],
    [],
  )

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Gastos
          <Button type="primary" icon={<PlusOutlined />} aria-label="Registrar gasto" onClick={() => { setEditing(null); setFormOpen(true) }}>
            Registrar
          </Button>
        </Space>
      </Typography.Title>
      <Space style={{ marginBottom: 16 }} wrap>
        <Space>
          <Typography.Text>Propiedad:</Typography.Text>
          <Select
            value={propertyId}
            onChange={(value) => setSelectedProperty(value)}
            options={properties.map((property) => ({ label: property.name, value: property.id }))}
            style={{ width: 240 }}
          />
        </Space>
        <Space>
          <Typography.Text>Año:</Typography.Text>
          <Select
            value={selectedYear}
            onChange={(value) => setSelectedYear(value)}
            options={Array.from({ length: 5 }, (_, i) => {
              const year = new Date().getFullYear() - 2 + i
              return { label: String(year), value: year }
            })}
            style={{ width: 100 }}
          />
        </Space>
        <Button icon={<BarChartOutlined />} loading={summaryQuery.isFetching} onClick={() => setSummaryRequested(true)}>
          Resumen
        </Button>
      </Space>
      {expensesQuery.isError && (
        <Typography.Text type="danger" style={{ display: 'block', marginBottom: 12 }}>
          Error al cargar gastos: {(expensesQuery.error as Error).message}
        </Typography.Text>
      )}
      <Spin spinning={expensesQuery.isLoading}>
        <Table rowKey="id" columns={columns} dataSource={expensesQuery.data ?? []} pagination={false} locale={{ emptyText }} />
      </Spin>
      {summary && (
        <Collapse
          style={{ marginTop: 16 }}
          items={[{
            key: 'summary',
            label: `Resumen ${summary.year}`,
            children: (
              <>
                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                  <Col xs={12} sm={6}><Card><Statistic title="Ingresos" value={fmtMoney(summary.total_income)} /></Card></Col>
                  <Col xs={12} sm={6}><Card><Statistic title="Gastos" value={fmtMoney(summary.total_expenses)} /></Card></Col>
                  <Col xs={12} sm={6}><Card><Statistic title="Deducibles" value={fmtMoney(summary.deductible_expenses)} /></Card></Col>
                  <Col xs={12} sm={6}><Card><Statistic title="Rentabilidad neta" value={fmtMoney(summary.net_profitability)} valueStyle={{ color: parseFloat(summary.net_profitability) >= 0 ? '#3f8600' : '#cf1322' }} /></Card></Col>
                </Row>
                <Descriptions title="Por categoría" column={2} size="small" bordered>
                  {Object.entries(summary.by_category).map(([category, amount]) => (
                    <Descriptions.Item key={category} label={expenseCategoryLabels[category] ?? category}>
                      {fmtMoney(amount)}
                    </Descriptions.Item>
                  ))}
                </Descriptions>
              </>
            ),
          }]}
        />
      )}
      <ExpenseForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={() => queryClient.invalidateQueries({ queryKey: ['expenses'] })}
        expense={editing}
      />
    </>
  )
}
