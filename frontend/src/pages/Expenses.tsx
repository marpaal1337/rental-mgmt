import { Button, Empty, message, Select, Space, Table, Tag, Typography, Spin } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchExpenses, fetchProperties } from '../api/endpoints'
import ExpenseForm from '../components/ExpenseForm'
import type { Expense, Property } from '../types'

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

  const load = useCallback((propertyId: number) => {
    setLoading(true)
    fetchExpenses(propertyId)
      .then(setExpenses)
      .catch(() => { setExpenses([]); message.error('Error al cargar gastos') })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    fetchProperties().then((p) => {
      setProperties(p)
      if (p.length > 0) {
        setSelectedProperty(p[0].id)
        load(p[0].id)
      } else {
        setLoading(false)
      }
    }).catch(() => message.error('Error al cargar propiedades'))
  }, [load])

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
      <Space style={{ marginBottom: 16 }}>
        <Typography.Text>Propiedad:</Typography.Text>
        <Select
          value={selectedProperty}
          onChange={(v) => {
            setSelectedProperty(v)
            load(v)
          }}
          options={properties.map((p) => ({ label: p.name, value: p.id }))}
          style={{ width: 240 }}
        />
      </Space>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={expenses} pagination={false} locale={{ emptyText }} />
      </Spin>
      <ExpenseForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={() => selectedProperty && load(selectedProperty)}
        expense={editing}
      />
    </>
  )
}
