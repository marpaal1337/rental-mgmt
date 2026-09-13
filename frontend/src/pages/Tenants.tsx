import type { ColumnsType } from 'antd/es/table'
import { fetchTenants } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import CrudPage from '../components/CrudPage'
import TenantForm from '../components/TenantForm'
import type { Tenant } from '../types'

const columns: ColumnsType<Tenant> = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: 'Nombre', dataIndex: 'name', key: 'name' },
  { title: 'Tipo Doc.', dataIndex: 'document_type', key: 'document_type' },
  { title: 'Número Doc.', dataIndex: 'document_number', key: 'document_number' },
  { title: 'Email', dataIndex: 'email', key: 'email' },
  { title: 'Teléfono', dataIndex: 'phone', key: 'phone' },
]

export default function Tenants() {
  return (
    <CrudPage
      title="Inquilinos"
      newLabel="Nuevo inquilino"
      emptyDescription="No hay inquilinos"
      queryKey={queryKeys.tenants}
      fetchFn={fetchTenants}
      columns={columns}
      FormComponent={TenantForm}
      errorMessage="Error al cargar inquilinos"
    />
  )
}
