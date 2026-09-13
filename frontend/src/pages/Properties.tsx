import { useQuery } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'
import { useMemo } from 'react'
import { fetchOwners, fetchProperties } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import CrudPage from '../components/CrudPage'
import PropertyForm from '../components/PropertyForm'
import type { Property } from '../types'

export default function Properties() {
  const { data: owners } = useQuery({
    queryKey: queryKeys.owners,
    queryFn: fetchOwners,
  })

  const ownerNames = useMemo(() => {
    const map: Record<number, string> = {}
    for (const owner of owners ?? []) map[owner.id] = owner.name
    return map
  }, [owners])

  const columns = useMemo<ColumnsType<Property>>(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
      { title: 'Nombre', dataIndex: 'name', key: 'name' },
      { title: 'Dirección', dataIndex: 'address', key: 'address' },
      { title: 'Ciudad', dataIndex: 'city', key: 'city' },
      { title: 'Provincia', dataIndex: 'province', key: 'province' },
      {
        title: 'Propietario',
        key: 'owner',
        render: (_: unknown, record: Property) => ownerNames[record.owner_id] ?? '-',
      },
    ],
    [ownerNames],
  )

  return (
    <CrudPage
      title="Propiedades"
      newLabel="Nueva propiedad"
      emptyDescription="No hay propiedades"
      queryKey={queryKeys.properties}
      fetchFn={fetchProperties}
      columns={columns}
      FormComponent={PropertyForm}
      errorMessage="Error al cargar propiedades"
    />
  )
}
