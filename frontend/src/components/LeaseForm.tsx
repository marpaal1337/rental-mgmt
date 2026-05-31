import { DatePicker, Form, Input, message, Modal, Select, Typography } from 'antd'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'
import { createLease, fetchOwners, fetchTenants, fetchUnits, updateLease } from '../api/endpoints'
import type { Lease, Owner, Tenant, Unit } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
  lease?: Lease | null
}

export default function LeaseForm({ open, onClose, onSaved, lease }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [owners, setOwners] = useState<Owner[]>([])
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [units, setUnits] = useState<Unit[]>([])

  const isEdit = !!lease

  useEffect(() => {
    if (open) {
      Promise.all([fetchOwners(), fetchTenants(), fetchUnits()])
        .then(([o, t, u]) => {
          setOwners(o)
          setTenants(t)
          setUnits(u)
        })
        .catch(() => message.error('Error al cargar datos de referencia'))
      if (lease) {
        form.setFieldsValue({
          ...lease,
          start_date: dayjs(lease.start_date),
          end_date: lease.end_date ? dayjs(lease.end_date) : null,
        })
      } else {
        form.resetFields()
      }
    }
  }, [open, lease, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const payload = {
        unit_id: values.unit_id,
        tenant_id: values.tenant_id,
        owner_id: values.owner_id,
        start_date: (values.start_date as dayjs.Dayjs).format('YYYY-MM-DD'),
        end_date: values.end_date ? (values.end_date as dayjs.Dayjs).format('YYYY-MM-DD') : null,
        is_active: values.is_active ?? true,
        notes: values.notes ?? null,
      }
      if (isEdit) {
        await updateLease(lease!.id, payload)
      } else {
        await createLease(payload)
      }
      onSaved()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error('Error al guardar el contrato')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Editar contrato' : 'Nuevo contrato'}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnClose
      width={520}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="tenant_id" label="Inquilino" rules={[{ required: true }]}>
          <Select
            showSearch
            placeholder="Seleccionar inquilino"
            options={tenants.map((t) => ({ label: t.name, value: t.id }))}
          />
        </Form.Item>
        <Form.Item name="owner_id" label="Propietario" rules={[{ required: true }]}>
          <Select
            showSearch
            placeholder="Seleccionar propietario"
            options={owners.map((o) => ({ label: o.name, value: o.id }))}
          />
        </Form.Item>
        <Form.Item name="unit_id" label="Unidad" rules={[{ required: true }]}>
          <Select
            showSearch
            placeholder="Seleccionar unidad"
            options={units.map((u) => ({ label: u.name, value: u.id }))}
          />
        </Form.Item>
        <Form.Item name="start_date" label="Fecha inicio" rules={[{ required: true }]}>
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="end_date" label="Fecha fin">
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        {isEdit && (
          <Form.Item name="is_active" label="Estado">
            <Select
              options={[
                { label: 'Activo', value: true },
                { label: 'Inactivo', value: false },
              ]}
            />
          </Form.Item>
        )}
        <Form.Item name="notes" label="Notas">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
      {!isEdit && (
        <Typography.Text type="secondary">
          Después de crear podrás configurar condiciones de renta, perfil fiscal y fianza.
        </Typography.Text>
      )}
    </Modal>
  )
}
