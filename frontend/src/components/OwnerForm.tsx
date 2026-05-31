import { Form, Input, message, Modal, Select } from 'antd'
import { useEffect, useState } from 'react'
import { createOwner, updateOwner } from '../api/endpoints'
import type { Owner, OwnerCreatePayload, OwnerUpdatePayload } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
  owner?: Owner | null
}

export default function OwnerForm({ open, onClose, onSaved, owner }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const isEdit = !!owner

  useEffect(() => {
    if (open) {
      if (owner) {
        form.setFieldsValue(owner)
      } else {
        form.resetFields()
      }
    }
  }, [open, owner, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const payload: OwnerCreatePayload = {
        name: values.name,
        document_type: values.document_type,
        document_number: values.document_number,
        email: values.email,
        phone: values.phone,
        address: values.address ?? null,
      }
      if (isEdit) {
        await updateOwner(owner!.id, payload as OwnerUpdatePayload)
      } else {
        await createOwner(payload)
      }
      onSaved()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error('Error al guardar el propietario')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Editar propietario' : 'Nuevo propietario'}
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
        <Form.Item name="document_type" label="Tipo documento" rules={[{ required: true }]}>
          <Select
            options={[
              { label: 'DNI', value: 'DNI' },
              { label: 'NIE', value: 'NIE' },
              { label: 'Pasaporte', value: 'Pasaporte' },
              { label: 'CIF', value: 'CIF' },
            ]}
          />
        </Form.Item>
        <Form.Item name="document_number" label="Número documento" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
          <Input type="email" />
        </Form.Item>
        <Form.Item name="phone" label="Teléfono" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="address" label="Dirección">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
