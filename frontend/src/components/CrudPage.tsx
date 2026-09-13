import { EditOutlined, PlusOutlined } from '@ant-design/icons'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Empty, Space, Spin, Table, Typography } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type { ComponentType } from 'react'
import { useMemo, useState } from 'react'

export interface CrudFormProps<T> {
  open: boolean
  onClose: () => void
  onSaved: () => void
  entity?: T | null
}

interface CrudPageProps<T extends { id: number }> {
  title: string
  newLabel: string
  emptyDescription: string
  queryKey: readonly unknown[]
  fetchFn: () => Promise<T[]>
  columns: ColumnsType<T>
  FormComponent: ComponentType<CrudFormProps<T>>
  errorMessage: string
}

export default function CrudPage<T extends { id: number }>({
  title,
  newLabel,
  emptyDescription,
  queryKey,
  fetchFn,
  columns,
  FormComponent,
  errorMessage,
}: CrudPageProps<T>) {
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<T | null>(null)
  const queryClient = useQueryClient()

  const { data, isLoading, isError, error } = useQuery({
    queryKey,
    queryFn: fetchFn,
  })

  const onSaved = () => {
    queryClient.invalidateQueries({ queryKey })
  }

  const allColumns = useMemo<ColumnsType<T>>(
    () => [
      ...columns,
      {
        title: '',
        key: 'actions',
        width: 60,
        render: (_: unknown, record: T) => (
          <Button
            type="link"
            icon={<EditOutlined />}
            aria-label="Editar"
            onClick={() => {
              setEditing(record)
              setFormOpen(true)
            }}
          />
        ),
      },
    ],
    [columns],
  )

  return (
    <>
      <Typography.Title level={3}>
        <Space align="center">
          {title}
          <Button
            type="primary"
            icon={<PlusOutlined />}
            aria-label={newLabel}
            onClick={() => {
              setEditing(null)
              setFormOpen(true)
            }}
          >
            {newLabel}
          </Button>
        </Space>
      </Typography.Title>
      {isError && (
        <Typography.Text type="danger" style={{ display: 'block', marginBottom: 12 }}>
          {errorMessage}: {(error as Error).message}
        </Typography.Text>
      )}
      <Spin spinning={isLoading}>
        <Table
          rowKey="id"
          columns={allColumns}
          dataSource={data ?? []}
          pagination={false}
          locale={{ emptyText: () => <Empty description={emptyDescription} /> }}
        />
      </Spin>
      <FormComponent
        open={formOpen}
        onClose={() => {
          setFormOpen(false)
          setEditing(null)
        }}
        onSaved={onSaved}
        entity={editing}
      />
    </>
  )
}
