import { Button, Empty, Space, Table, Tag, Typography, Spin, message } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { fetchProperties, fetchUnits } from '../api/endpoints'
import UnitForm from '../components/UnitForm'
import type { Property, Unit } from '../types'

const emptyText = () => <Empty description="No hay unidades" />

const unitTypeLabels: Record<string, string> = {
  vivienda: 'Vivienda',
  local: 'Local',
  garage: 'Garaje',
  trastero: 'Trastero',
}

export default function Units() {
  const [units, setUnits] = useState<Unit[]>([])
  const [properties, setProperties] = useState<Property[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Unit | null>(null)

  const load = () => {
    setLoading(true)
    Promise.all([fetchUnits(), fetchProperties()])
      .then(([u, p]) => {
        setUnits(u)
        setProperties(p)
      })
      .catch(() => message.error('Error al cargar unidades'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    Promise.all([fetchUnits(), fetchProperties()])
      .then(([u, p]) => {
        setUnits(u)
        setProperties(p)
      })
      .catch(() => message.error('Error al cargar unidades'))
      .finally(() => setLoading(false))
  }, [])

  const propertyMap = useMemo(() => {
    const map: Record<number, string> = {}
    properties.forEach((p) => { map[p.id] = p.name })
    return map
  }, [properties])

  const columns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: 'Propiedad',
      key: 'property',
      render: (_: unknown, r: Unit) => propertyMap[r.property_id] ?? '-',
    },
    { title: 'Nombre', dataIndex: 'name', key: 'name' },
    {
      title: 'Tipo',
      dataIndex: 'unit_type',
      key: 'unit_type',
      render: (v: string) => unitTypeLabels[v] ?? v,
    },
    {
      title: 'Área m²',
      dataIndex: 'area_m2',
      key: 'area_m2',
      render: (v: number | null) => (v != null ? v : '-'),
    },
    {
      title: 'Activo',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v: boolean) =>
        v ? <Tag color="green">Sí</Tag> : <Tag color="default">No</Tag>,
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: Unit) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          aria-label="Editar unidad"
          onClick={() => {
            setEditing(r)
            setFormOpen(true)
          }}
        />
      ),
    },
  ], [propertyMap])

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Unidades
          <Button type="primary" icon={<PlusOutlined />} aria-label="Nueva unidad" onClick={() => { setEditing(null); setFormOpen(true) }}>
            Nueva
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={units} pagination={false} locale={{ emptyText }} />
      </Spin>
      <UnitForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={load}
        unit={editing}
      />
    </>
  )
}
