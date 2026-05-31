import { Button, Empty, Space, Table, Typography, Spin, message } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { fetchOwners } from '../api/endpoints'
import OwnerForm from '../components/OwnerForm'
import type { Owner } from '../types'

const emptyText = () => <Empty description="No hay propietarios" />

export default function Owners() {
  const [owners, setOwners] = useState<Owner[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Owner | null>(null)

  const load = () => {
    setLoading(true)
    fetchOwners().then(setOwners).catch(() => message.error('Error al cargar propietarios')).finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchOwners().then(setOwners).catch(() => message.error('Error al cargar propietarios')).finally(() => setLoading(false))
  }, [])

  const columns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Nombre', dataIndex: 'name', key: 'name' },
    { title: 'Tipo Doc.', dataIndex: 'document_type', key: 'document_type' },
    { title: 'Número Doc.', dataIndex: 'document_number', key: 'document_number' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    { title: 'Teléfono', dataIndex: 'phone', key: 'phone' },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: Owner) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          aria-label="Editar propietario"
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
          Propietarios
          <Button type="primary" icon={<PlusOutlined />} aria-label="Nuevo propietario" onClick={() => { setEditing(null); setFormOpen(true) }}>
            Nuevo
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={owners} pagination={false} locale={{ emptyText }} />
      </Spin>
      <OwnerForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={load}
        owner={editing}
      />
    </>
  )
}
