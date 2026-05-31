import { Form, Input, message, Modal, Select } from 'antd'
import { useEffect, useState } from 'react'
import { createTenant, updateTenant } from '../api/endpoints'
import type { Tenant, TenantCreatePayload, TenantUpdatePayload } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
  tenant?: Tenant | null
}

export default function TenantForm({ open, onClose, onSaved, tenant }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const isEdit = !!tenant

  useEffect(() => {
    if (open) {
      if (tenant) {
        form.setFieldsValue(tenant)
      } else {
        form.resetFields()
      }
    }
  }, [open, tenant, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const payload: TenantCreatePayload | TenantUpdatePayload = {
        name: values.name,
        document_type: values.document_type,
        document_number: values.document_number,
        email: values.email,
        phone: values.phone,
      }
      if (isEdit) {
        await updateTenant(tenant!.id, payload as TenantUpdatePayload)
      } else {
        await createTenant(payload as TenantCreatePayload)
      }
      onSaved()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error('Error al guardar el inquilino')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Editar inquilino' : 'Nuevo inquilino'}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnClose
      width={520}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="Nombre" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="document_type" label="Tipo de documento" rules={[{ required: true }]}>
          <Select
            options={[
              { label: 'DNI', value: 'DNI' },
              { label: 'NIE', value: 'NIE' },
              { label: 'Pasaporte', value: 'Pasaporte' },
              { label: 'CIF', value: 'CIF' },
            ]}
          />
        </Form.Item>
        <Form.Item name="document_number" label="Número de documento" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
          <Input type="email" />
        </Form.Item>
        <Form.Item name="phone" label="Teléfono" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  )
}
