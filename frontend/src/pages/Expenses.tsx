import { Button, Card, Col, Collapse, Descriptions, Empty, message, Row, Select, Space, Table, Tag, Typography, Spin, Statistic } from 'antd'
import { PlusOutlined, EditOutlined, BarChartOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchExpenses, fetchExpenseSummary, fetchProperties } from '../api/endpoints'
import ExpenseForm from '../components/ExpenseForm'
import type { Expense, ExpenseSummary, Property } from '../types'

const categoryLabels: Record<string, string> = {
  community: 'Comunidad',
  repairs: 'Reparaciones',
  supplies: 'Suministros',
  taxes: 'Impuestos',
  insurance: 'Seguros',
  admin_fees: 'Gastos gestión',
  other: 'Otros',
}

const emptyText = () => <Empty description="No hay gastos" />

export default function Expenses() {
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Expense | null>(null)
  const [properties, setProperties] = useState<Property[]>([])
  const [selectedProperty, setSelectedProperty] = useState<number | null>(null)
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear())
  const [summary, setSummary] = useState<ExpenseSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  const load = useCallback((propertyId: number, year?: number) => {
    setLoading(true)
    fetchExpenses(propertyId, year)
      .then(setExpenses)
      .catch(() => { setExpenses([]); message.error('Error al cargar gastos') })
      .finally(() => setLoading(false))
  }, [])

  const loadSummary = useCallback((propertyId: number, year: number) => {
    setSummaryLoading(true)
    fetchExpenseSummary(propertyId, year)
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setSummaryLoading(false))
  }, [])

  useEffect(() => {
    fetchProperties().then((p) => {
      setProperties(p)
      if (p.length > 0) {
        const firstId = p[0].id
        setSelectedProperty(firstId)
        load(firstId, selectedYear)
      } else {
        setLoading(false)
      }
    }).catch(() => message.error('Error al cargar propiedades'))
  }, [])

  const columns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: 'Categoría',
      dataIndex: 'category',
      key: 'category',
      render: (v: string) => categoryLabels[v] ?? v,
    },
    {
      title: 'Importe',
      dataIndex: 'amount',
      key: 'amount',
      render: (v: string) => `${parseFloat(v).toFixed(2)} €`,
    },
    { title: 'Fecha', dataIndex: 'expense_date', key: 'expense_date' },
    {
      title: 'Deducible',
      dataIndex: 'deductible',
      key: 'deductible',
      render: (v: boolean) =>
        v ? <Tag color="green">Sí</Tag> : <Tag color="red">No</Tag>,
    },
    {
      title: 'Proveedor',
      dataIndex: 'supplier',
      key: 'supplier',
      render: (v: string | null) => v ?? '-',
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: Expense) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          aria-label="Editar gasto"
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
            value={selectedProperty}
            onChange={(v) => {
              setSelectedProperty(v)
              load(v, selectedYear)
            }}
            options={properties.map((p) => ({ label: p.name, value: p.id }))}
            style={{ width: 240 }}
          />
        </Space>
        <Space>
          <Typography.Text>Año:</Typography.Text>
          <Select
            value={selectedYear}
            onChange={(v) => {
              setSelectedYear(v)
              if (selectedProperty) load(selectedProperty, v)
            }}
            options={Array.from({ length: 5 }, (_, i) => {
              const y = new Date().getFullYear() - 2 + i
              return { label: String(y), value: y }
            })}
            style={{ width: 100 }}
          />
        </Space>
        <Button icon={<BarChartOutlined />} loading={summaryLoading} onClick={() => selectedProperty && loadSummary(selectedProperty, selectedYear)}>
          Resumen
        </Button>
      </Space>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={expenses} pagination={false} locale={{ emptyText }} />
      </Spin>
      {summary && (
        <Collapse items={[{
          key: 'summary',
          label: `Resumen ${summary.year}`,
          children: (
            <>
              <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                <Col xs={12} sm={6}><Card><Statistic title="Ingresos" value={parseFloat(summary.total_income).toFixed(2)} suffix="€" /></Card></Col>
                <Col xs={12} sm={6}><Card><Statistic title="Gastos" value={parseFloat(summary.total_expenses).toFixed(2)} suffix="€" /></Card></Col>
                <Col xs={12} sm={6}><Card><Statistic title="Deducibles" value={parseFloat(summary.deductible_expenses).toFixed(2)} suffix="€" /></Card></Col>
                <Col xs={12} sm={6}><Card><Statistic title="Rentabilidad neta" value={parseFloat(summary.net_profitability).toFixed(2)} suffix="€" valueStyle={{ color: parseFloat(summary.net_profitability) >= 0 ? '#3f8600' : '#cf1322' }} /></Card></Col>
              </Row>
              <Descriptions title="Por categoría" column={2} size="small" bordered>
                {Object.entries(summary.by_category).map(([cat, amount]) => (
                  <Descriptions.Item key={cat} label={cat}>{parseFloat(amount).toFixed(2)} €</Descriptions.Item>
                ))}
              </Descriptions>
            </>
          ),
        }]} />
      )}
      <ExpenseForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={() => selectedProperty && load(selectedProperty, selectedYear)}
        expense={editing}
      />
    </>
  )
}
