import { CheckOutlined, UploadOutlined } from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Empty, Modal, Spin, Table, Tabs, Tag, Typography, Upload, message } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo, useState } from 'react'
import {
  confirmMatch, fetchAllMovements, fetchUnmatchedMovements,
  importBankCsv, proposeMatches,
} from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import type { BankMovement, Reconciliation } from '../types'
import { fmtMoney } from '../utils/format'
import { movementStatusColors, movementStatusLabels } from '../utils/labels'

const emptyText = () => <Empty description="Sin datos" />

export default function ReconciliationPage() {
  const queryClient = useQueryClient()
  const [candidates, setCandidates] = useState<Reconciliation[]>([])
  const [candidatesOpen, setCandidatesOpen] = useState(false)

  const unmatchedQuery = useQuery({
    queryKey: queryKeys.unmatchedMovements,
    queryFn: fetchUnmatchedMovements,
  })
  const allQuery = useQuery({
    queryKey: queryKeys.allMovements,
    queryFn: fetchAllMovements,
  })

  const invalidateMovements = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.unmatchedMovements })
    queryClient.invalidateQueries({ queryKey: queryKeys.allMovements })
  }

  const importMutation = useMutation({
    mutationFn: importBankCsv,
    onSuccess: (movements) => {
      message.success(`${movements.length} movimientos importados`)
      invalidateMovements()
    },
    onError: (error: Error) => message.error(error.message),
  })

  const proposeMutation = useMutation({
    mutationFn: proposeMatches,
    onSuccess: (reconciliations) => {
      if (reconciliations.length === 0) {
        message.info('No se encontraron coincidencias con pagos existentes')
        return
      }
      setCandidates(reconciliations)
      setCandidatesOpen(true)
      invalidateMovements()
    },
    onError: (error: Error) => message.error(error.message),
  })

  const confirmMutation = useMutation({
    mutationFn: confirmMatch,
    onSuccess: (_data, reconciliationId) => {
      message.success('Coincidencia confirmada')
      setCandidates((previous) => previous.filter((candidate) => candidate.id !== reconciliationId))
      setCandidatesOpen(false)
      invalidateMovements()
    },
    onError: (error: Error) => message.error(error.message),
  })

  const unmatchedColumns = useMemo<ColumnsType<BankMovement>>(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
      { title: 'Fecha', dataIndex: 'entry_date', key: 'entry_date' },
      {
        title: 'Importe',
        dataIndex: 'amount',
        key: 'amount',
        render: (value: string) => fmtMoney(value),
      },
      { title: 'Concepto', dataIndex: 'concept', key: 'concept', ellipsis: true },
      {
        title: '',
        key: 'actions',
        width: 120,
        render: (_: unknown, record: BankMovement) => (
          <Button
            type="primary"
            size="small"
            aria-label="Proponer coincidencias"
            loading={proposeMutation.isPending && proposeMutation.variables === record.id}
            onClick={() => proposeMutation.mutate(record.id)}
          >
            Proponer
          </Button>
        ),
      },
    ],
    [proposeMutation],
  )

  const allColumns = useMemo<ColumnsType<BankMovement>>(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
      { title: 'Fecha', dataIndex: 'entry_date', key: 'entry_date' },
      {
        title: 'Importe',
        dataIndex: 'amount',
        key: 'amount',
        render: (value: string) => fmtMoney(value),
      },
      { title: 'Concepto', dataIndex: 'concept', key: 'concept', ellipsis: true },
      {
        title: 'Estado',
        dataIndex: 'status',
        key: 'status',
        render: (value: string) => (
          <Tag color={movementStatusColors[value] ?? 'default'}>
            {movementStatusLabels[value] ?? value}
          </Tag>
        ),
      },
    ],
    [],
  )

  const candidateColumns = useMemo<ColumnsType<Reconciliation>>(
    () => [
      { title: 'Pago ID', dataIndex: 'payment_id', key: 'payment_id' },
      {
        title: 'Score',
        dataIndex: 'score',
        key: 'score',
        render: (value: string) => `${(parseFloat(value) * 100).toFixed(0)}%`,
      },
      {
        title: '',
        key: 'actions',
        width: 100,
        render: (_: unknown, record: Reconciliation) => (
          <Button
            type="primary"
            size="small"
            icon={<CheckOutlined />}
            loading={confirmMutation.isPending && confirmMutation.variables === record.id}
            aria-label="Confirmar coincidencia"
            onClick={() => confirmMutation.mutate(record.id)}
          >
            Confirmar
          </Button>
        ),
      },
    ],
    [confirmMutation],
  )

  const tabs = [
    {
      key: 'import',
      label: 'Importar CSV',
      children: (
        <div style={{ padding: 24 }}>
          <Upload.Dragger
            accept=".csv"
            showUploadList={false}
            disabled={importMutation.isPending}
            beforeUpload={(file) => { importMutation.mutate(file); return false }}
          >
            <p className="ant-upload-drag-icon"><UploadOutlined /></p>
            <p className="ant-upload-text">Haz clic o arrastra un CSV bancario aquí</p>
            <p className="ant-upload-hint">Formato ING España o CSV genérico</p>
          </Upload.Dragger>
        </div>
      ),
    },
    {
      key: 'unmatched',
      label: `Sin procesar (${unmatchedQuery.data?.length ?? 0})`,
      children: (
        <Spin spinning={unmatchedQuery.isLoading}>
          <Table rowKey="id" columns={unmatchedColumns} dataSource={unmatchedQuery.data ?? []} pagination={false} locale={{ emptyText }} />
        </Spin>
      ),
    },
    {
      key: 'all',
      label: 'Todos',
      children: (
        <Table rowKey="id" columns={allColumns} dataSource={allQuery.data ?? []} pagination={false} locale={{ emptyText }} />
      ),
    },
  ]

  return (
    <>
      <Typography.Title level={3}>Conciliación bancaria</Typography.Title>
      <Tabs items={tabs} />
      <Modal
        title="Coincidencias propuestas"
        open={candidatesOpen}
        onCancel={() => setCandidatesOpen(false)}
        footer={null}
        width={520}
      >
        <Table rowKey="id" columns={candidateColumns} dataSource={candidates} pagination={false} />
      </Modal>
    </>
  )
}
