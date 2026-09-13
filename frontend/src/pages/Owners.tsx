import type { ColumnsType } from 'antd/es/table'
import { fetchOwners } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import CrudPage from '../components/CrudPage'
import OwnerForm from '../components/OwnerForm'
import type { Owner } from '../types'

const columns: ColumnsType<Owner> = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: 'Nombre', dataIndex: 'name', key: 'name' },
  { title: 'Tipo Doc.', dataIndex: 'document_type', key: 'document_type' },
  { title: 'Número Doc.', dataIndex: 'document_number', key: 'document_number' },
  { title: 'Email', dataIndex: 'email', key: 'email' },
  { title: 'Teléfono', dataIndex: 'phone', key: 'phone' },
]

export default function Owners() {
  return (
    <CrudPage
      title="Propietarios"
      newLabel="Nuevo propietario"
      emptyDescription="No hay propietarios"
      queryKey={queryKeys.owners}
      fetchFn={fetchOwners}
      columns={columns}
      FormComponent={OwnerForm}
      errorMessage="Error al cargar propietarios"
    />
  )
}
