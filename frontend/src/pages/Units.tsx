import { Button, Empty, Space, Table, Tag, Typography, Spin, message } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useRef, useState } from 'react'
import { fetchProperties, fetchUnits } from '../api/endpoints'
import UnitForm from '../components/UnitForm'
import type { Unit } from '../types'

const emptyText = () => <Empty description="No hay unidades" />

const unitTypeLabels: Record<string, string> = {
  vivienda: 'Vivienda',
  local: 'Local',
  garage: 'Garaje',
  trastero: 'Trastero',
}

export default function Units() {
  const [units, setUnits] = useState<Unit[]>([])
  const [propertyMap, setPropertyMap] = useState<Record<number, string>>({})
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Unit | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    const m = mountedRef
    m.current = true
    Promise.all([fetchUnits(), fetchProperties()])
      .then(([u, p]) => {
        if (!m.current) return
        setUnits(u)
        const map: Record<number, string> = {}
        p.forEach((prop) => { map[prop.id] = prop.name })
        setPropertyMap(map)
      })
      .catch(() => { if (m.current) message.error('Error al cargar unidades') })
      .finally(() => { if (m.current) setLoading(false) })
    return () => { m.current = false }
  }, [])

  const load = () => {
    setLoading(true)
    Promise.all([fetchUnits(), fetchProperties()])
      .then(([u, p]) => {
        setUnits(u)
        const map: Record<number, string> = {}
        p.forEach((prop) => { map[prop.id] = prop.name })
        setPropertyMap(map)
      })
      .catch(() => message.error('Error al cargar unidades'))
      .finally(() => setLoading(false))
  }

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
