import { Button, Empty, Space, Table, Typography, Spin, message } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import { fetchTenants } from '../api/endpoints'
import TenantForm from '../components/TenantForm'
import type { Tenant } from '../types'

const emptyText = () => <Empty description="No hay inquilinos" />

export default function Tenants() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Tenant | null>(null)

  const load = () => {
    setLoading(true)
    fetchTenants().then(setTenants).catch(() => message.error('Error al cargar inquilinos')).finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchTenants().then(setTenants).catch(() => message.error('Error al cargar inquilinos')).finally(() => setLoading(false))
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
      render: (_: unknown, r: Tenant) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          aria-label="Editar inquilino"
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
          Inquilinos
          <Button type="primary" icon={<PlusOutlined />} aria-label="Nuevo inquilino" onClick={() => { setEditing(null); setFormOpen(true) }}>
            Nuevo
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={tenants} pagination={false} locale={{ emptyText }} />
      </Spin>
      <TenantForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={load}
        tenant={editing}
      />
    </>
  )
}
