import {
  Button, DatePicker, Descriptions, Empty, Form, Input, InputNumber,
  message, Modal, Spin, Switch, Table, Tabs, Tag, Typography,
} from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  applyIndex, createRentCondition, fetchDeposit, fetchIndexUpdates,
  fetchLease, fetchRentConditions, fetchTaxProfile, upsertDeposit, upsertTaxProfile,
} from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import type {
  DepositUpdatePayload, IndexUpdate, RentCondition, TaxProfileUpdatePayload,
} from '../types'
import { fmtMoney } from '../utils/format'

const emptyText = () => <Empty description="Sin datos" />

export default function LeaseDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const leaseId = Number(id)
  const queryClient = useQueryClient()

  const [rcModalOpen, setRcModalOpen] = useState(false)
  const [rcForm] = Form.useForm()
  const [tpForm] = Form.useForm()
  const [depForm] = Form.useForm()
  const [iuModalOpen, setIuModalOpen] = useState(false)
  const [iuForm] = Form.useForm()

  const leaseQuery = useQuery({
    queryKey: queryKeys.lease(leaseId),
    queryFn: () => fetchLease(leaseId),
  })
  const rcQuery = useQuery({
    queryKey: queryKeys.rentConditions(leaseId),
    queryFn: () => fetchRentConditions(leaseId),
  })
  const iuQuery = useQuery({
    queryKey: queryKeys.indexUpdates(leaseId),
    queryFn: () => fetchIndexUpdates(leaseId),
  })
  const tpQuery = useQuery({
    queryKey: queryKeys.taxProfile(leaseId),
    queryFn: () => fetchTaxProfile(leaseId),
    retry: false,
  })
  const depositQuery = useQuery({
    queryKey: queryKeys.deposit(leaseId),
    queryFn: () => fetchDeposit(leaseId),
    retry: false,
  })

  useEffect(() => {
    if (tpQuery.data) tpForm.setFieldsValue(tpQuery.data)
  }, [tpQuery.data, tpForm])

  useEffect(() => {
    if (depositQuery.data) {
      depForm.setFieldsValue({
        ...depositQuery.data,
        deposit_date: dayjs(depositQuery.data.deposit_date),
        return_date: depositQuery.data.return_date ? dayjs(depositQuery.data.return_date) : null,
      })
    }
  }, [depositQuery.data, depForm])

  const createRcMutation = useMutation({
    mutationFn: (values: { start_date: dayjs.Dayjs; monthly_rent: number; notes?: string }) =>
      createRentCondition(leaseId, {
        start_date: values.start_date.format('YYYY-MM-DD'),
        monthly_rent: String(values.monthly_rent),
        notes: values.notes ?? null,
      }),
    onSuccess: () => {
      message.success('Condición de renta creada')
      setRcModalOpen(false)
      rcForm.resetFields()
      queryClient.invalidateQueries({ queryKey: queryKeys.rentConditions(leaseId) })
    },
    onError: (error: Error) => message.error(error.message),
  })

  const saveTpMutation = useMutation({
    mutationFn: (payload: TaxProfileUpdatePayload) => upsertTaxProfile(leaseId, payload),
    onSuccess: () => {
      message.success('Perfil fiscal guardado')
      queryClient.invalidateQueries({ queryKey: queryKeys.taxProfile(leaseId) })
    },
    onError: (error: Error) => message.error(error.message),
  })

  const saveDepositMutation = useMutation({
    mutationFn: (payload: DepositUpdatePayload) => upsertDeposit(leaseId, payload),
    onSuccess: () => {
      message.success('Fianza guardada')
      queryClient.invalidateQueries({ queryKey: queryKeys.deposit(leaseId) })
    },
    onError: (error: Error) => message.error(error.message),
  })

  const applyIndexMutation = useMutation({
    mutationFn: (values: { application_date: dayjs.Dayjs; index_rate: number; index_name?: string; notes?: string }) =>
      applyIndex(leaseId, {
        index_rate: String(values.index_rate),
        application_date: values.application_date.format('YYYY-MM-DD'),
        index_name: values.index_name ?? 'IPC',
        notes: values.notes ?? null,
      }),
    onSuccess: () => {
      message.success('Revisión aplicada')
      setIuModalOpen(false)
      iuForm.resetFields()
      queryClient.invalidateQueries({ queryKey: queryKeys.rentConditions(leaseId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.indexUpdates(leaseId) })
    },
    onError: (error: Error) => message.error(error.message),
  })

  const rcColumns = useMemo<ColumnsType<RentCondition>>(
    () => [
      { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
      { title: 'Fecha inicio', dataIndex: 'start_date', key: 'start_date' },
      { title: 'Renta mensual', dataIndex: 'monthly_rent', key: 'monthly_rent', render: (v: string) => fmtMoney(v) },
      { title: 'Notas', dataIndex: 'notes', key: 'notes', render: (v: string | null) => v ?? '-' },
    ],
    [],
  )

  const iuColumns = useMemo<ColumnsType<IndexUpdate>>(
    () => [
      { title: 'Fecha', dataIndex: 'application_date', key: 'application_date' },
      { title: 'Renta anterior', dataIndex: 'previous_rent', key: 'previous_rent', render: (v: string) => fmtMoney(v) },
      { title: 'Renta nueva', dataIndex: 'new_rent', key: 'new_rent', render: (v: string) => fmtMoney(v) },
      { title: 'Índice', dataIndex: 'index_rate', key: 'index_rate', render: (v: string) => `${(parseFloat(v) * 100).toFixed(2)}%` },
      { title: 'Nombre', dataIndex: 'index_name', key: 'index_name' },
      { title: 'Notas', dataIndex: 'notes', key: 'notes', render: (v: string | null) => v ?? '-' },
    ],
    [],
  )

  const handleRcOk = async () => {
    const values = await rcForm.validateFields()
    createRcMutation.mutate(values)
  }

  const handleTpSave = async () => {
    const values = await tpForm.validateFields()
    const payload: TaxProfileUpdatePayload = {}
    if (values.vat_rate !== undefined) payload.vat_rate = String(values.vat_rate)
    if (values.irpf_rate !== undefined) payload.irpf_rate = String(values.irpf_rate)
    if (values.vat_exempt !== undefined) payload.vat_exempt = values.vat_exempt
    if (values.withholding_applies !== undefined) payload.withholding_applies = values.withholding_applies
    saveTpMutation.mutate(payload)
  }

  const handleDepSave = async () => {
    const values = await depForm.validateFields()
    const payload: DepositUpdatePayload = {
      amount: String(values.amount),
      agency: values.agency,
      deposit_date: (values.deposit_date as dayjs.Dayjs).format('YYYY-MM-DD'),
    }
    if (values.return_date) payload.return_date = (values.return_date as dayjs.Dayjs).format('YYYY-MM-DD')
    saveDepositMutation.mutate(payload)
  }

  const handleIuOk = async () => {
    const values = await iuForm.validateFields()
    applyIndexMutation.mutate(values)
  }

  if (leaseQuery.isLoading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />
  if (leaseQuery.isError || !leaseQuery.data) return <Typography.Text type="danger">Contrato no encontrado</Typography.Text>

  const lease = leaseQuery.data

  const tabs = [
    {
      key: 'rent',
      label: 'Renta',
      children: (
        <Spin spinning={rcQuery.isLoading}>
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={() => setRcModalOpen(true)}>Nueva condición</Button>
          </div>
          <Table rowKey="id" columns={rcColumns} dataSource={rcQuery.data ?? []} pagination={false} locale={{ emptyText }} />
        </Spin>
      ),
    },
    {
      key: 'tax',
      label: 'Fiscal',
      children: (
        <Spin spinning={tpQuery.isLoading}>
          {tpQuery.data ? (
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
              <Button type="primary" loading={saveTpMutation.isPending} onClick={handleTpSave}>Guardar</Button>
            </Form>
          ) : (
            <Typography.Text type="secondary">No hay perfil fiscal configurado. Usa la pestaña Renta o la API para crearlo.</Typography.Text>
          )}
        </Spin>
      ),
    },
    {
      key: 'deposit',
      label: 'Fianza',
      children: (
        <Spin spinning={depositQuery.isLoading}>
          {depositQuery.data ? (
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
              <Button type="primary" loading={saveDepositMutation.isPending} onClick={handleDepSave}>Guardar</Button>
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
        <Spin spinning={iuQuery.isLoading}>
          <div style={{ marginBottom: 16 }}>
            <Button type="primary" onClick={() => setIuModalOpen(true)}>Aplicar revisión</Button>
          </div>
          <Table rowKey="id" columns={iuColumns} dataSource={iuQuery.data ?? []} pagination={false} locale={{ emptyText }} />
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
        <Descriptions.Item label="Inquilino">{lease.tenant_name ?? lease.tenant?.name ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="Propietario">{lease.owner_name ?? lease.owner?.name ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="Unidad">{lease.unit_name ?? lease.unit?.name ?? '-'}</Descriptions.Item>
        <Descriptions.Item label="Estado">
          <Tag color={lease.is_active ? 'green' : 'default'}>{lease.is_active ? 'Activo' : 'Inactivo'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Inicio">{lease.start_date}</Descriptions.Item>
        <Descriptions.Item label="Fin">{lease.end_date ?? 'Indefinido'}</Descriptions.Item>
        {lease.notes && <Descriptions.Item label="Notas" span={2}>{lease.notes}</Descriptions.Item>}
      </Descriptions>
      <Tabs items={tabs} />
      <Modal title="Nueva condición de renta" open={rcModalOpen} onOk={handleRcOk} onCancel={() => setRcModalOpen(false)} confirmLoading={createRcMutation.isPending} destroyOnHidden width={400}>
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
      <Modal title="Aplicar revisión IPC" open={iuModalOpen} onOk={handleIuOk} onCancel={() => setIuModalOpen(false)} confirmLoading={applyIndexMutation.isPending} destroyOnHidden width={400}>
        <Form form={iuForm} layout="vertical">
          <Form.Item name="application_date" label="Fecha aplicación" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="index_rate" label="Índice (ej. 0.03 = 3%)" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} min={-0.99} max={0.5} step={0.001} />
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
