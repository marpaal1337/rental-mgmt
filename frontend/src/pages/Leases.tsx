import { Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { fetchLeases } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import CrudPage from '../components/CrudPage'
import LeaseForm from '../components/LeaseForm'
import type { Lease } from '../types'

const columns: ColumnsType<Lease> = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  {
    title: 'Inquilino',
    key: 'tenant',
    render: (_: unknown, record: Lease) => record.tenant_name ?? record.tenant?.name ?? '-',
  },
  {
    title: 'Propietario',
    key: 'owner',
    render: (_: unknown, record: Lease) => record.owner_name ?? record.owner?.name ?? '-',
  },
  {
    title: 'Unidad',
    key: 'unit',
    render: (_: unknown, record: Lease) => record.unit_name ?? record.unit?.name ?? '-',
  },
  { title: 'Inicio', dataIndex: 'start_date', key: 'start_date' },
  {
    title: 'Fin',
    dataIndex: 'end_date',
    key: 'end_date',
    render: (value: string | null) => value ?? 'Indefinido',
  },
  {
    title: 'Estado',
    dataIndex: 'is_active',
    key: 'is_active',
    render: (value: boolean) =>
      value ? <Tag color="green">Activo</Tag> : <Tag color="default">Inactivo</Tag>,
  },
]

export default function Leases() {
  return (
    <CrudPage
      title="Contratos"
      newLabel="Nuevo contrato"
      emptyDescription="No hay contratos"
      queryKey={queryKeys.leases}
      fetchFn={fetchLeases}
      columns={columns}
      FormComponent={LeaseForm}
      errorMessage="Error al cargar contratos"
    />
  )
}
