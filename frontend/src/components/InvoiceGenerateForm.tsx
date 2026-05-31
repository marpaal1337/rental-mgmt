import { DatePicker, Form, message, Modal, Typography } from 'antd'
import dayjs from 'dayjs'
import { useState } from 'react'
import { generateInvoices } from '../api/endpoints'

interface Props {
  open: boolean
  onClose: () => void
  onGenerated: () => void
}

export default function InvoiceGenerateForm({ open, onClose, onGenerated }: Props) {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)

  const handleOk = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      const period = (values.period as dayjs.Dayjs).format('YYYY-MM')
      await generateInvoices({ period })
      message.success('Facturas generadas correctamente')
      onGenerated()
      onClose()
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) {
        return
      }
      message.error('Error al generar facturas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      title="Generar facturas"
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      confirmLoading={loading}
      destroyOnClose
      width={400}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="period"
          label="Periodo"
          rules={[{ required: true, message: 'Selecciona el mes' }]}
        >
          <DatePicker picker="month" style={{ width: '100%' }} />
        </Form.Item>
      </Form>
      <Typography.Text type="secondary">
        Se generarán facturas para todos los contratos activos con condiciones de renta vigentes.
      </Typography.Text>
    </Modal>
  )
}
