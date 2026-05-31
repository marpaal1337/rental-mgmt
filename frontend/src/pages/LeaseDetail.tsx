import {
  Button, DatePicker, Descriptions, Empty, Form, Input, InputNumber,
  message, Modal, Spin, Switch, Table, Tabs, Tag, Typography,
} from 'antd'
import dayjs from 'dayjs'
import { useEffect, useMemo, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  applyIndex, createRentCondition, fetchDeposit, fetchIndexUpdates,
  fetchLease, fetchRentConditions, fetchTaxProfile, upsertDeposit, upsertTaxProfile,
} from '../api/endpoints'
import type {
  Deposit, DepositUpdatePayload, IndexUpdate, Lease, RentCondition, TaxProfile, TaxProfileUpdatePayload,
} from '../types'

const emptyText = () => <Empty description="Sin datos" />

export default function LeaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const leaseId = Number(id)

  const [lease, setLease] = useState<Lease | null>(null)
  const [loading, setLoading] = useState(true)

  const [rentConditions, setRentConditions] = useState<RentCondition[]>([])
  const [rcLoading, setRcLoading] = useState(true)
  const [rcModalOpen, setRcModalOpen] = useState(false)
  const [rcForm] = Form.useForm()
  const [rcSaving, setRcSaving] = useState(false)

  const [taxProfile, setTaxProfile] = useState<TaxProfile | null>(null)
  const [tpLoading, setTpLoading] = useState(true)
  const [tpForm] = Form.useForm()
  const [tpSaving, setTpSaving] = useState(false)

  const [deposit, setDeposit] = useState<Deposit | null>(null)
  const [depLoading, setDepLoading] = useState(true)
  const [depForm] = Form.useForm()
  const [depSaving, setDepSaving] = useState(false)

  const [indexUpdates, setIndexUpdates] = useState<IndexUpdate[]>([])
  const [iuLoading, setIuLoading] = useState(true)
  const [iuModalOpen, setIuModalOpen] = useState(false)
  const [iuForm] = Form.useForm()
  const [iuSaving, setIuSaving] = useState(false)

  const loadRc = () => {
    fetchRentConditions(leaseId).then(setRentConditions).catch(() => message.error('Error al cargar condiciones de renta')).finally(() => setRcLoading(false))
  }

  const loadIu = () => {
    fetchIndexUpdates(leaseId).then(setIndexUpdates).catch(() => message.error('Error al cargar revisiones IPC')).finally(() => setIuLoading(false))
  }

  useEffect(() => {
    fetchLease(leaseId).then(setLease).catch(() => message.error('Error al cargar el contrato')).finally(() => setLoading(false))
    fetchRentConditions(leaseId).then(setRentConditions).catch(() => message.error('Error al cargar condiciones de renta')).finally(() => setRcLoading(false))
    fetchIndexUpdates(leaseId).then(setIndexUpdates).catch(() => message.error('Error al cargar revisiones IPC')).finally(() => setIuLoading(false))
  }, [leaseId])

  useEffect(() => {
    fetchTaxProfile(leaseId).then((tp) => {
      setTaxProfile(tp)
      tpForm.setFieldsValue(tp)
    }).catch(() => setTaxProfile(null)).finally(() => setTpLoading(false))
  }, [leaseId])

  useEffect(() => {
    fetchDeposit(leaseId).then((d) => {
      setDeposit(d)
      depForm.setFieldsValue({ ...d, deposit_date: dayjs(d.deposit_date), return_date: d.return_date ? dayjs(d.return_date) : null })
    }).catch(() => setDeposit(null)).finally(() => setDepLoading(false))
  }, [leaseId])

  const rcColumns = useMemo(() => [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Fecha inicio', dataIndex: 'start_date', key: 'start_date' },
    { title: 'Renta mensual', dataIndex: 'monthly_rent', key: 'monthly_rent', render: (v: string) => `${parseFloat(v).toFixed(2)} €` },
    { title: 'Notas', dataIndex: 'notes', key: 'notes', render: (v: string | null) => v ?? '-' },
  ], [])

  const iuColumns = useMemo(() => [
    { title: 'Fecha', dataIndex: 'application_date', key: 'application_date' },
    { title: 'Renta anterior', dataIndex: 'previous_rent', key: 'previous_rent', render: (v: string) => `${parseFloat(v).toFixed(2)} €` },
    { title: 'Renta nueva', dataIndex: 'new_rent', key: 'new_rent', render: (v: string) => `${parseFloat(v).toFixed(2)} €` },
    { title: 'Índice', dataIndex: 'index_rate', key: 'index_rate', render: (v: string) => `${(parseFloat(v) * 100).toFixed(2)}%` },
    { title: 'Nombre', dataIndex: 'index_name', key: 'index_name' },
    { title: 'Notas', dataIndex: 'notes', key: 'notes', render: (v: string | null) => v ?? '-' },
  ], [])

  const handleRcOk = async () => {
    try {
      const values = await rcForm.validateFields()
      setRcSaving(true)
      await createRentCondition(leaseId, {
        start_date: (values.start_date as dayjs.Dayjs).format('YYYY-MM-DD'),
        monthly_rent: String(values.monthly_rent),
        notes: values.notes ?? null,
      })
      message.success('Condición de renta creada')
      setRcModalOpen(false)
      rcForm.resetFields()
      loadRc()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error('Error al guardar')
    } finally {
      setRcSaving(false)
    }
  }

  const handleTpSave = async () => {
    try {
      const values = await tpForm.validateFields()
      setTpSaving(true)
      const payload: TaxProfileUpdatePayload = {}
      if (values.vat_rate !== undefined) payload.vat_rate = String(values.vat_rate)
      if (values.irpf_rate !== undefined) payload.irpf_rate = String(values.irpf_rate)
      if (values.vat_exempt !== undefined) payload.vat_exempt = values.vat_exempt
      if (values.withholding_applies !== undefined) payload.withholding_applies = values.withholding_applies
      const tp = await upsertTaxProfile(leaseId, payload)
      setTaxProfile(tp)
      message.success('Perfil fiscal guardado')
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error('Error al guardar perfil fiscal')
    } finally {
      setTpSaving(false)
    }
  }

  const handleDepSave = async () => {
    try {
      const values = await depForm.validateFields()
      setDepSaving(true)
      const payload: DepositUpdatePayload = {
        amount: String(values.amount),
        agency: values.agency,
        deposit_date: (values.deposit_date as dayjs.Dayjs).format('YYYY-MM-DD'),
      }
      if (values.return_date) payload.return_date = (values.return_date as dayjs.Dayjs).format('YYYY-MM-DD')
      const d = await upsertDeposit(leaseId, payload)
      setDeposit(d)
      message.success('Fianza guardada')
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error('Error al guardar fianza')
    } finally {
      setDepSaving(false)
    }
  }

  const handleIuOk = async () => {
    try {
      const values = await iuForm.validateFields()
      setIuSaving(true)
      await applyIndex(leaseId, {
        index_rate: String(values.index_rate),
        application_date: (values.application_date as dayjs.Dayjs).format('YYYY-MM-DD'),
        index_name: values.index_name ?? 'IPC',
        notes: values.notes ?? null,
      })
      message.success('Revisión aplicada')
      setIuModalOpen(false)
      iuForm.resetFields()
      loadIu()
      loadRc()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return
      message.error('Error al aplicar revisión')
    } finally {
      setIuSaving(false)
    }
  }

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />
  if (!lease) return <Typography.Text type="danger">Contrato no encontrado</Typography.Text>

  const tabs = [
    {
      key: 'rent',
      label: 'Renta',
      children: (
        <Spin spinning={rcLoading}>
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={() => setRcModalOpen(true)}>Nueva condición</Button>
          </div>
          <Table rowKey="id" columns={rcColumns} dataSource={rentConditions} pagination={false} locale={{ emptyText }} />
        </Spin>
      ),
    },
    {
      key: 'tax',
      label: 'Fiscal',
      children: (
        <Spin spinning={tpLoading}>
          {taxProfile ? (
            <Form form={tpForm} layout="vertical" style={{ maxWidth: 400 }}>
              <Form.Item name="vat_rate" label="IVA %">
                <InputNumber style={{ width: '100%' }} min={0} max={100} step={0.01} />
              </Form.Item>
              <Form.Item name="irpf_rate" label="IRPF %">
                <InputNumber style={{ width: '100%' }} min={0} max={100} step={0.01} />
              </Form.Item>
              <Form.Item name="vat_exempt" label="Exento IVA" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Form.Item name="withholding_applies" label="Aplica retención" valuePropName="checked">
                <Switch />
              </Form.Item>
              <Button type="primary" loading={tpSaving} onClick={handleTpSave}>Guardar</Button>
            </Form>
          ) : (
            <Typography.Text type="secondary">No hay perfil fiscal configurado. Crea una condición de renta primero.</Typography.Text>
          )}
        </Spin>
      ),
    },
    {
      key: 'deposit',
      label: 'Fianza',
      children: (
        <Spin spinning={depLoading}>
          {deposit ? (
            <Form form={depForm} layout="vertical" style={{ maxWidth: 400 }}>
              <Form.Item name="amount" label="Importe" rules={[{ required: true }]}>
                <InputNumber style={{ width: '100%' }} min={0} step={0.01} prefix="€" />
              </Form.Item>
              <Form.Item name="deposit_date" label="Fecha depósito" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
              <Form.Item name="agency" label="Organismo" rules={[{ required: true }]}>
                <Input />
              </Form.Item>
              <Form.Item name="return_date" label="Fecha devolución">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
              <Button type="primary" loading={depSaving} onClick={handleDepSave}>Guardar</Button>
            </Form>
          ) : (
            <Typography.Text type="secondary">No hay fianza registrada.</Typography.Text>
          )}
        </Spin>
      ),
    },
    {
      key: 'ipc',
      label: 'IPC',
      children: (
        <Spin spinning={iuLoading}>
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={() => setIuModalOpen(true)}>Aplicar revisión</Button>
          </div>
          <Table rowKey="id" columns={iuColumns} dataSource={indexUpdates} pagination={false} locale={{ emptyText }} />
        </Spin>
      ),
    },
  ]

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button type="link" onClick={() => navigate('/leases')} style={{ padding: 0, marginBottom: 8 }}>← Volver a contratos</Button>
        <Typography.Title level={3} style={{ margin: 0 }}>Detalle del contrato #{lease.id}</Typography.Title>
      </div>
      <Descriptions column={2} bordered size="small" style={{ marginBottom: 24 }}>
        <Descriptions.Item label="Inquilino">{lease.tenant?.name ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="Propietario">{lease.owner?.name ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="Unidad">{lease.unit?.name ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="Estado">
          <Tag color={lease.is_active ? 'green' : 'default'}>{lease.is_active ? 'Activo' : 'Inactivo'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Inicio">{lease.start_date}</Descriptions.Item>
        <Descriptions.Item label="Fin">{lease.end_date ?? 'Indefinido'}</Descriptions.Item>
        {lease.notes && <Descriptions.Item label="Notas" span={2}>{lease.notes}</Descriptions.Item>}
      </Descriptions>
      <Tabs items={tabs} />
      <Modal title="Nueva condición de renta" open={rcModalOpen} onOk={handleRcOk} onCancel={() => setRcModalOpen(false)} confirmLoading={rcSaving} destroyOnClose width={400}>
        <Form form={rcForm} layout="vertical">
          <Form.Item name="start_date" label="Fecha inicio" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="monthly_rent" label="Renta mensual" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} prefix="€" />
          </Form.Item>
          <Form.Item name="notes" label="Notas">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
      <Modal title="Aplicar revisión IPC" open={iuModalOpen} onOk={handleIuOk} onCancel={() => setIuModalOpen(false)} confirmLoading={iuSaving} destroyOnClose width={400}>
        <Form form={iuForm} layout="vertical">
          <Form.Item name="application_date" label="Fecha aplicación" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="index_rate" label="Índice (%)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={0} step={0.01} />
          </Form.Item>
          <Form.Item name="index_name" label="Nombre del índice" initialValue="IPC">
            <Input />
          </Form.Item>
          <Form.Item name="notes" label="Notas">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
