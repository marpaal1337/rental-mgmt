import { Button, Empty, Space, Table, Typography, Spin, message } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { fetchOwners, fetchProperties } from '../api/endpoints'
import PropertyForm from '../components/PropertyForm'
import type { Owner, Property } from '../types'

const emptyText = () => <Empty description="No hay propiedades" />

export default function Properties() {
  const [properties, setProperties] = useState<Property[]>([])
  const [owners, setOwners] = useState<Owner[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Property | null>(null)

  const load = () => {
    setLoading(true)
    Promise.all([fetchProperties(), fetchOwners()])
      .then(([p, o]) => {
        setProperties(p)
        setOwners(o)
      })
      .catch(() => message.error('Error al cargar datos'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    Promise.all([fetchProperties(), fetchOwners()])
      .then(([p, o]) => {
        setProperties(p)
        setOwners(o)
      })
      .catch(() => message.error('Error al cargar datos'))
      .finally(() => setLoading(false))
  }, [])

  const ownerMap = useMemo(() => {
    const map: Record<number, string> = {}
    for (const o of owners) {
      map[o.id] = o.name
    }
    return map
  }, [owners])

  const columns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Nombre', dataIndex: 'name', key: 'name' },
    { title: 'Dirección', dataIndex: 'address', key: 'address' },
    { title: 'Ciudad', dataIndex: 'city', key: 'city' },
    { title: 'Provincia', dataIndex: 'province', key: 'province' },
    {
      title: 'Propietario',
      key: 'owner',
      render: (_: unknown, r: Property) => ownerMap[r.owner_id] ?? '-',
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: Property) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          aria-label="Editar propiedad"
          onClick={() => {
            setEditing(r)
            setFormOpen(true)
          }}
        />
      ),
    },
  ], [ownerMap])

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Propiedades
          <Button type="primary" icon={<PlusOutlined />} aria-label="Nueva propiedad" onClick={() => { setEditing(null); setFormOpen(true) }}>
            Nueva
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={properties} pagination={false} locale={{ emptyText }} />
      </Spin>
      <PropertyForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={load}
        property={editing}
      />
    </>
  )
}
