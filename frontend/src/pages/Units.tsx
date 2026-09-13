import { useQuery } from '@tanstack/react-query'
import { Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo } from 'react'
import { fetchProperties, fetchUnits } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import CrudPage from '../components/CrudPage'
import UnitForm from '../components/UnitForm'
import type { Unit } from '../types'
import { unitTypeLabels } from '../utils/labels'

export default function Units() {
  const { data: properties } = useQuery({
    queryKey: queryKeys.properties,
    queryFn: fetchProperties,
  })

  const propertyNames = useMemo(() => {
    const map: Record<number, string> = {}
    for (const property of properties ?? []) map[property.id] = property.name
    return map
  }, [properties])

  const columns = useMemo<ColumnsType<Unit>>(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
      {
        title: 'Propiedad',
        key: 'property',
        render: (_: unknown, record: Unit) => propertyNames[record.property_id] ?? '-',
      },
      { title: 'Nombre', dataIndex: 'name', key: 'name' },
      {
        title: 'Tipo',
        dataIndex: 'unit_type',
        key: 'unit_type',
        render: (value: string) => unitTypeLabels[value] ?? value,
      },
      {
        title: 'Área m²',
        dataIndex: 'area_m2',
        key: 'area_m2',
        render: (value: number | null) => (value != null ? value : '-'),
      },
      {
        title: 'Activo',
        dataIndex: 'is_active',
        key: 'is_active',
        render: (value: boolean) =>
          value ? <Tag color="green">Sí</Tag> : <Tag color="default">No</Tag>,
      },
    ],
    [propertyNames],
  )

  return (
    <CrudPage
      title="Unidades"
      newLabel="Nueva unidad"
      emptyDescription="No hay unidades"
      queryKey={queryKeys.units}
      fetchFn={fetchUnits}
      columns={columns}
      FormComponent={UnitForm}
      errorMessage="Error al cargar unidades"
    />
  )
}
