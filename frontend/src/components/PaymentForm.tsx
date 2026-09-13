import { DatePicker, Form, Input, InputNumber, message, Modal, Select } from 'antd'
import dayjs from 'dayjs'
import { useEffect, useState } from 'react'
import { createPayment, fetchInvoices, updatePayment } from '../api/endpoints'
import type { Invoice, Payment } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  onSaved: () => void
  entity?: Payment | null
}

const METHODS = [
  { label: 'Transferencia', value: 'transferencia' },
  { label: 'Tarjeta', value: 'tarjeta' },
  { label: 'Efectivo', value: 'efectivo' },
  { label: 'Domiciliación', value: 'domiciliacion' },
]

export default function PaymentForm({ open, onClose, onSaved, entity }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [invoices, setInvoices] = useState<Invoice[]>([])

  const isEdit = !!entity

  useEffect(() => {
    if (open) {
      fetchInvoices()
        .then(setInvoices)
        .catch(() => message.error('Error al cargar facturas'))
      if (entity) {
        form.setFieldsValue({
          ...entity,
          amount: parseFloat(entity.amount),
          payment_date: dayjs(entity.payment_date),
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
      const payload = {
        invoice_id: values.invoice_id,
        amount: String(values.amount),
        payment_date: (values.payment_date as dayjs.Dayjs).format('YYYY-MM-DD'),
        method: values.method,
        notes: values.notes ?? null,
      }
      if (isEdit) {
        await updatePayment(entity!.id, payload)
      } else {
        await createPayment(payload)
      }
      onSaved()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error(err instanceof Error ? err.message : 'Error al guardar el pago')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title={isEdit ? 'Editar pago' : 'Registrar pago'}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnHidden
      width={480}
    >
      <Form form={form} layout="vertical">
        <Form.Item name="invoice_id" label="Factura" rules={[{ required: true }]}>
          <Select
            showSearch
            placeholder="Seleccionar factura"
            options={invoices.map((inv) => ({
              label: `#${inv.id} - ${inv.period} (${parseFloat(inv.total).toFixed(2)} €)`,
              value: inv.id,
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
        <Form.Item name="payment_date" label="Fecha" rules={[{ required: true }]}>
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="method" label="Método" rules={[{ required: true }]}>
          <Select options={METHODS} />
        </Form.Item>
        <Form.Item name="notes" label="Notas">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>
    </Modal>
  )
}
