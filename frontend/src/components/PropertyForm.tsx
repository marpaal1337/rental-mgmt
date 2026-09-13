import { Form, Input, message, Modal, Select } from 'antd'
import { useEffect, useState } from 'react'
import { createProperty, fetchOwners, updateProperty } from '../api/endpoints'
import type { Owner, Property, PropertyCreatePayload, PropertyUpdatePayload } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
  entity?: Property | null
}

export default function PropertyForm({ open, onClose, onSaved, entity }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [owners, setOwners] = useState<Owner[]>([])

  const isEdit = !!entity

  useEffect(() => {
    if (open) {
      fetchOwners()
        .then(setOwners)
        .catch(() => message.error('Error al cargar propietarios'))
      if (entity) {
        form.setFieldsValue(entity)
      } else {
        form.resetFields()
      }
    }
  }, [open, entity, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const payload: PropertyCreatePayload = {
        name: values.name,
        address: values.address,
        city: values.city,
        province: values.province,
        zip_code: values.zip_code,
        cadastral_ref: values.cadastral_ref ?? null,
        owner_id: values.owner_id,
      }
      if (isEdit) {
        await updateProperty(entity!.id, payload as PropertyUpdatePayload)
      } else {
        await createProperty(payload)
      }
      onSaved()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error(err instanceof Error ? err.message : 'Error al guardar la propiedad')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Editar propiedad' : 'Nueva propiedad'}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnHidden
      width={520}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="name" label="Nombre" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="address" label="Dirección" rules={[{ required: true }]}>
          <Input autoComplete="street-address" />
        </Form.Item>
        <Form.Item name="city" label="Ciudad" rules={[{ required: true }]}>
          <Input autoComplete="address-level2" />
        </Form.Item>
        <Form.Item name="province" label="Provincia" rules={[{ required: true }]}>
          <Input autoComplete="address-level1" />
        </Form.Item>
        <Form.Item name="zip_code" label="Código postal" rules={[{ required: true }]}>
          <Input autoComplete="postal-code" inputMode="numeric" />
        </Form.Item>
        <Form.Item name="cadastral_ref" label="Referencia catastral">
          <Input />
        </Form.Item>
        <Form.Item name="owner_id" label="Propietario" rules={[{ required: true }]}>
          <Select
            showSearch
            placeholder="Seleccionar propietario"
            options={owners.map((o) => ({ label: o.name, value: o.id }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}
