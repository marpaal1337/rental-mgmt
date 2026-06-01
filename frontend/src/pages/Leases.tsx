import { Button, Empty, Space, Table, Tag, Typography, Spin } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useMemo, useState } from 'react'
import { fetchLeases } from '../api/endpoints'
import LeaseForm from '../components/LeaseForm'
import { useFetch } from '../hooks/useFetch'
import type { Lease } from '../types'

const emptyText = () => <Empty description="No hay contratos" />

export default function Leases() {
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Lease | null>(null)
  const { data: leases, loading, load } = useFetch(() => fetchLeases())

  const columns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: 'Inquilino',
      key: 'tenant',
      render: (_: unknown, r: Lease) => r.tenant?.name ?? '-',
    },
    {
      title: 'Propietario',
      key: 'owner',
      render: (_: unknown, r: Lease) => r.owner?.name ?? '-',
    },
    {
      title: 'Unidad',
      key: 'unit',
      render: (_: unknown, r: Lease) => r.unit?.name ?? '-',
    },
    { title: 'Inicio', dataIndex: 'start_date', key: 'start_date' },
    {
      title: 'Fin',
      dataIndex: 'end_date',
      key: 'end_date',
      render: (v: string | null) => v ?? 'Indefinido',
    },
    {
      title: 'Estado',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (v: boolean) =>
        v ? <Tag color="green">Activo</Tag> : <Tag color="default">Inactivo</Tag>,
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, r: Lease) => (
        <Button
          type="link"
          icon={<EditOutlined />}
          aria-label="Editar contrato"
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
          Contratos
          <Button type="primary" icon={<PlusOutlined />} aria-label="Nuevo contrato" onClick={() => { setEditing(null); setFormOpen(true) }}>
            Nuevo
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={leases ?? []} pagination={false} locale={{ emptyText }} />
      </Spin>
      <LeaseForm
        open={formOpen}
        onClose={() => { setFormOpen(false); setEditing(null) }}
        onSaved={load}
        lease={editing}
      />
    </>
  )
}
