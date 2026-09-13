import { Form, Input, InputNumber, message, Modal, Select, Switch } from 'antd'
import { useEffect, useState } from 'react'
import { createUnit, fetchProperties, updateUnit } from '../api/endpoints'
import type { Property, Unit, UnitCreatePayload, UnitUpdatePayload } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
  entity?: Unit | null
}

export default function UnitForm({ open, onClose, onSaved, entity }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [properties, setProperties] = useState<Property[]>([])

  const isEdit = !!entity

  useEffect(() => {
    if (open) {
      fetchProperties()
        .then(setProperties)
        .catch(() => message.error('Error al cargar propiedades'))
      if (entity) {
        form.setFieldsValue({
          ...entity,
          area_m2: entity.area_m2 ? parseFloat(String(entity.area_m2)) : null,
          is_active: entity.is_active,
        })
      } else {
        form.resetFields()
      }
    }
  }, [open, entity, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const payload: UnitCreatePayload | UnitUpdatePayload = {
        property_id: values.property_id,
        name: values.name,
        unit_type: values.unit_type,
        area_m2: values.area_m2 ?? null,
        is_active: values.is_active ?? true,
      }
      if (isEdit) {
        await updateUnit(entity!.id, payload as UnitUpdatePayload)
      } else {
        await createUnit(payload as UnitCreatePayload)
      }
      onSaved()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error(err instanceof Error ? err.message : 'Error al guardar la unidad')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Editar unidad' : 'Nueva unidad'}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnHidden
      width={520}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="property_id" label="Propiedad" rules={[{ required: true }]}>
          <Select
            showSearch
            placeholder="Seleccionar propiedad"
            options={properties.map((p) => ({ label: p.name, value: p.id }))}
          />
        </Form.Item>
        <Form.Item name="name" label="Nombre" rules={[{ required: true }]}>
          <Input placeholder="Ej: 1º A" />
        </Form.Item>
        <Form.Item name="unit_type" label="Tipo" rules={[{ required: true }]}>
          <Select
            options={[
              { label: 'Vivienda', value: 'vivienda' },
              { label: 'Local', value: 'local' },
              { label: 'Garaje', value: 'garage' },
              { label: 'Trastero', value: 'trastero' },
            ]}
          />
        </Form.Item>
        <Form.Item name="area_m2" label="Área (m²)">
          <InputNumber step={0.1} min={0} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="is_active" label="Activa" valuePropName="checked">
          <Switch defaultChecked />
        </Form.Item>
      </Form>
    </Modal>
  )
}
