import { DatePicker, Form, Input, InputNumber, message, Modal, Select, Switch } from 'antd'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'
import { createExpense, fetchExpenseCategories, fetchProperties, updateExpense } from '../api/endpoints'
import type { Expense, Property } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
  expense?: Expense | null
}

const CATEGORY_LABELS: Record<string, string> = {
  community: 'Comunidad',
  repairs: 'Reparaciones',
  supplies: 'Suministros',
  taxes: 'Impuestos',
  insurance: 'Seguros',
  admin_fees: 'Gastos gestión',
  other: 'Otros',
}

export default function ExpenseForm({ open, onClose, onSaved, expense }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [properties, setProperties] = useState<Property[]>([])
  const [categories, setCategories] = useState<string[]>([])

  const isEdit = !!expense

  useEffect(() => {
    if (open) {
      Promise.all([fetchProperties(), fetchExpenseCategories()])
        .then(([p, c]) => {
          setProperties(p)
          setCategories(c)
        })
        .catch(() => message.error('Error al cargar datos de referencia'))
      if (expense) {
        form.setFieldsValue({
          ...expense,
          amount: parseFloat(expense.amount),
          expense_date: dayjs(expense.expense_date),
        })
      } else {
        form.resetFields()
      }
    }
  }, [open, expense, form])

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const payload = {
        property_id: values.property_id,
        category: values.category,
        amount: String(values.amount),
        expense_date: (values.expense_date as dayjs.Dayjs).format('YYYY-MM-DD'),
        deductible: values.deductible ?? true,
        supplier: values.supplier ?? null,
        notes: values.notes ?? null,
      }
      if (isEdit) {
        await updateExpense(expense!.id, payload)
      } else {
        await createExpense(payload)
      }
      onSaved()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error('Error al guardar el gasto')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Editar gasto' : 'Registrar gasto'}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnClose
      width={480}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="property_id" label="Propiedad" rules={[{ required: true }]}>
          <Select
            showSearch
            placeholder="Seleccionar propiedad"
            options={properties.map((p) => ({ label: p.name, value: p.id }))}
          />
        </Form.Item>
        <Form.Item name="category" label="Categoría" rules={[{ required: true }]}>
          <Select
            options={categories.map((c) => ({
              label: CATEGORY_LABELS[c] ?? c,
              value: c,
            }))}
          />
        </Form.Item>
        <Form.Item name="amount" label="Importe" rules={[{ required: true }]}>
          <InputNumber
            style={{ width: '100%' }}
            min={0.01}
            step={0.01}
            prefix="€"
          />
        </Form.Item>
        <Form.Item name="expense_date" label="Fecha" rules={[{ required: true }]}>
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="deductible" label="Deducible" valuePropName="checked">
          <Switch defaultChecked />
        </Form.Item>
        <Form.Item name="supplier" label="Proveedor">
          <Input />
        </Form.Item>
        <Form.Item name="notes" label="Notas">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
