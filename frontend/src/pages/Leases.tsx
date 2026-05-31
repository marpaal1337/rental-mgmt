import { Button, Space, Table, Tag, Typography, Spin } from 'antd'
import { PlusOutlined, EditOutlined } from '@ant-design/icons'
import { useEffect, useState } from 'react'
import { fetchLeases } from '../api/endpoints'
import LeaseForm from '../components/LeaseForm'
import type { Lease } from '../types'

export default function Leases() {
  const [leases, setLeases] = useState<Lease[]>([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Lease | null>(null)

  const load = () => {
    setLoading(true)
    fetchLeases().then(setLeases).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const columns = [
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
          onClick={() => {
            setEditing(r)
            setFormOpen(true)
          }}
        />
      ),
    },
  ]

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          Contratos
          <Button type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); setFormOpen(true) }}>
            Nuevo
          </Button>
        </Space>
      </Typography.Title>
      <Spin spinning={loading}>
        <Table rowKey="id" columns={columns} dataSource={leases} pagination={false} />
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
