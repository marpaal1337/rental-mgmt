import { Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { fetchPayments } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import CrudPage from '../components/CrudPage'
import PaymentForm from '../components/PaymentForm'
import type { Payment } from '../types'
import { fmtMoney } from '../utils/format'
import { paymentMethodColors } from '../utils/labels'

const columns: ColumnsType<Payment> = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: 'Factura', dataIndex: 'invoice_id', key: 'invoice_id' },
  {
    title: 'Importe',
    dataIndex: 'amount',
    key: 'amount',
    render: (value: string) => fmtMoney(value),
  },
  { title: 'Fecha', dataIndex: 'payment_date', key: 'payment_date' },
  {
    title: 'Método',
    dataIndex: 'method',
    key: 'method',
    render: (value: string) => (
      <Tag color={paymentMethodColors[value] ?? 'default'}>{value}</Tag>
    ),
  },
  {
    title: 'Notas',
    dataIndex: 'notes',
    key: 'notes',
    render: (value: string | null) => value ?? '-',
  },
]

export default function Payments() {
  return (
    <CrudPage
      title="Pagos"
      newLabel="Registrar pago"
      emptyDescription="No hay pagos"
      queryKey={queryKeys.payments}
      fetchFn={fetchPayments}
      columns={columns}
      FormComponent={PaymentForm}
      errorMessage="Error al cargar pagos"
    />
  )
}
