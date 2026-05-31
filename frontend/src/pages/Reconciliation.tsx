import { Button, Empty, Modal, Spin, Table, Tag, Tabs, Typography, Upload, message } from 'antd'
import { CheckOutlined, UploadOutlined } from '@ant-design/icons'
import { useEffect, useMemo, useState } from 'react'
import {
  confirmMatch, fetchAllMovements, fetchUnmatchedMovements,
  importBankCsv, proposeMatches,
} from '../api/endpoints'
import type { BankMovement, Reconciliation } from '../types'

const statusColors: Record<string, string> = {
  unmatched: 'orange',
  proposed: 'blue',
  confirmed: 'green',
}

const statusLabels: Record<string, string> = {
  unmatched: 'Sin procesar',
  proposed: 'Propuesto',
  confirmed: 'Confirmado',
}

const emptyText = () => <Empty description="Sin datos" />

export default function Reconciliation() {
  const [unmatched, setUnmatched] = useState<BankMovement[]>([])
  const [allMovements, setAllMovements] = useState<BankMovement[]>([])
  const [loading, setLoading] = useState(false)
  const [candidates, setCandidates] = useState<Reconciliation[]>([])
  const [candidatesOpen, setCandidatesOpen] = useState(false)
  const [confirming, setConfirming] = useState<number | null>(null)

  const loadData = () => {
    setLoading(true)
    Promise.all([
      fetchUnmatchedMovements(),
      fetchAllMovements(),
    ]).then(([u, a]) => {
      setUnmatched(u)
      setAllMovements(a)
    }).catch(() => message.error('Error al cargar datos')).finally(() => setLoading(false))
  }

  useEffect(() => {
    Promise.all([
      fetchUnmatchedMovements(),
      fetchAllMovements(),
    ]).then(([u, a]) => {
      setUnmatched(u)
      setAllMovements(a)
    }).catch(() => message.error('Error al cargar datos')).finally(() => setLoading(false))
  }, [])

  const handleImport = async (file: File) => {
    try {
      const result = await importBankCsv(file)
      message.success(`${result.length} movimientos importados`)
      loadData()
    } catch {
      message.error('Error al importar CSV')
    }
    return false
  }

  const handlePropose = async (movementId: number) => {
    try {
      const recs = await proposeMatches(movementId)
      if (recs.length === 0) {
        message.info('No se encontraron coincidencias con pagos existentes')
        return
      }
      setCandidates(recs)
      setCandidatesOpen(true)
      loadData()
    } catch {
      message.error('Error al proponer coincidencias')
    }
  }

  const handleConfirm = async (reconciliationId: number) => {
    setConfirming(reconciliationId)
    try {
      await confirmMatch(reconciliationId)
      message.success('Coincidencia confirmada')
      setCandidates((prev) => prev.filter((c) => c.id !== reconciliationId))
      if (candidates.length <= 1) setCandidatesOpen(false)
      loadData()
    } catch {
      message.error('Error al confirmar')
    } finally {
      setConfirming(null)
    }
  }

  const uncoveredColumns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Fecha', dataIndex: 'entry_date', key: 'entry_date' },
    {
      title: 'Importe',
      dataIndex: 'amount',
      key: 'amount',
      render: (v: string) => `${parseFloat(v).toFixed(2)} €`,
    },
    { title: 'Concepto', dataIndex: 'concept', key: 'concept', ellipsis: true },
    {
      title: '',
      key: 'actions',
      width: 120,
      render: (_: unknown, r: BankMovement) => (
        <Button type="primary" size="small" aria-label="Proponer coincidencias" onClick={() => handlePropose(r.id)}>
          Proponer
        </Button>
      ),
    },
  ], [])

  const allColumns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Fecha', dataIndex: 'entry_date', key: 'entry_date' },
    {
      title: 'Importe',
      dataIndex: 'amount',
      key: 'amount',
      render: (v: string) => `${parseFloat(v).toFixed(2)} €`,
    },
    { title: 'Concepto', dataIndex: 'concept', key: 'concept', ellipsis: true },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (v: string) => <Tag color={statusColors[v] ?? 'default'}>{statusLabels[v] ?? v}</Tag>,
    },
  ], [])

  const candidateColumns = useMemo(() => [
    { title: 'Pago ID', dataIndex: 'payment_id', key: 'payment_id' },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      render: (v: string) => `${(parseFloat(v) * 100).toFixed(0)}%`,
    },
    {
      title: '',
      key: 'actions',
      width: 100,
      render: (_: unknown, r: Reconciliation) => (
        <Button
          type="primary"
          size="small"
          icon={<CheckOutlined />}
          loading={confirming === r.id}
          aria-label="Confirmar coincidencia"
          onClick={() => handleConfirm(r.id)}
        >
          Confirmar
        </Button>
      ),
    },
  ], [confirming])

  const tabs = [
    {
      key: 'import',
      label: 'Importar CSV',
      children: (
        <div style={{ padding: 24 }}>
          <Upload.Dragger accept=".csv" showUploadList={false} beforeUpload={(f) => { handleImport(f); return false }}>
            <p className="ant-upload-drag-icon"><UploadOutlined /></p>
            <p className="ant-upload-text">Haz clic o arrastra un CSV bancario aquí</p>
            <p className="ant-upload-hint">Formato ING España o CSV genérico</p>
          </Upload.Dragger>
        </div>
      ),
    },
    {
      key: 'unmatched',
      label: `Sin procesar (${unmatched.length})`,
      children: (
        <Spin spinning={loading}>
          <Table rowKey="id" columns={uncoveredColumns} dataSource={unmatched} pagination={false} locale={{ emptyText }} />
        </Spin>
      ),
    },
    {
      key: 'all',
      label: 'Todos',
      children: (
        <Table rowKey="id" columns={allColumns} dataSource={allMovements} pagination={false} locale={{ emptyText }} />
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
