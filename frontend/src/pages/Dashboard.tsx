import {
  FileTextOutlined, HomeOutlined, MoneyCollectOutlined, ShoppingCartOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Card, Col, Empty, Row, Spin, Tag, Typography } from 'antd'
import dayjs from 'dayjs'
import { useMemo } from 'react'
import type { ReactNode } from 'react'
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { fetchExpenses, fetchInvoices, fetchPayments, fetchStats } from '../api/endpoints'
import { queryKeys } from '../api/queryKeys'
import type { DashboardStats } from '../types'
import { fmtMoney } from '../utils/format'

const MONTH_NAMES: Record<string, string> = {
  '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr',
  '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic',
}

function getLast6Months(): string[] {
  const result: string[] = []
  for (let i = 5; i >= 0; i--) {
    result.push(dayjs().subtract(i, 'month').format('YYYY-MM'))
  }
  return result
}

interface ChartTooltipEntry {
  name?: string
  value?: number | string
  color?: string
}

interface ChartTooltipProps {
  active?: boolean
  payload?: ChartTooltipEntry[]
  label?: string
}

function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#fff',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-sm)',
      padding: '10px 14px',
      boxShadow: 'var(--shadow-md)',
      fontSize: 'var(--fs-sm)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4, color: 'var(--color-text-primary)' }}>{label}</div>
      {payload.map((entry) => (
        <div key={entry.name} style={{ color: entry.color, marginBottom: 2 }}>
          {entry.name}: {Number(entry.value).toFixed(2)} €
        </div>
      ))}
    </div>
  )
}

interface GradientCard {
  title: string
  value: (stats: DashboardStats | undefined) => number
  icon: ReactNode
  gradient: string
  shadow: string
}

const GRADIENT_CARDS: GradientCard[] = [
  {
    title: 'Contratos activos',
    value: (stats) => stats?.active_leases ?? 0,
    icon: <FileTextOutlined />,
    gradient: 'linear-gradient(135deg, #1A6B6B 0%, #248A8A 100%)',
    shadow: '0 4px 16px rgba(26, 107, 107, 0.25)',
  },
  {
    title: 'Facturas este mes',
    value: (stats) => stats?.month_invoices ?? 0,
    icon: <ShoppingCartOutlined />,
    gradient: 'linear-gradient(135deg, #C1704A 0%, #D4895E 100%)',
    shadow: '0 4px 16px rgba(193, 112, 74, 0.25)',
  },
  {
    title: 'Pagos este mes',
    value: (stats) => stats?.month_payments ?? 0,
    icon: <MoneyCollectOutlined />,
    gradient: 'linear-gradient(135deg, #D4943A 0%, #E0A84C 100%)',
    shadow: '0 4px 16px rgba(212, 148, 58, 0.25)',
  },
  {
    title: 'Gastos este año',
    value: (stats) => stats?.year_expenses ?? 0,
    icon: <HomeOutlined />,
    gradient: 'linear-gradient(135deg, #6B8F3A 0%, #82A94A 100%)',
    shadow: '0 4px 16px rgba(107, 143, 58, 0.25)',
  },
]

export default function Dashboard() {
  const currentYear = dayjs().year()
  const { data, isLoading, isError, error } = useQuery({
    queryKey: [...queryKeys.stats, currentYear],
    queryFn: async () => {
      const [stats, invoices, expenses, payments] = await Promise.all([
        fetchStats(),
        fetchInvoices(),
        fetchExpenses(undefined, currentYear),
        fetchPayments(),
      ])
      return { stats, invoices, expenses, payments }
    },
  })

  const chartData = useMemo(() => {
    if (!data?.invoices || !data?.expenses) return []
    return getLast6Months().map((month) => {
      const [, monthNum] = month.split('-')
      const income = data.invoices
        .filter((invoice) => invoice.period.startsWith(month) && (invoice.status === 'paid' || invoice.status === 'partial'))
        .reduce((sum, invoice) => sum + Number(invoice.total), 0)
      const monthExpenses = data.expenses
        .filter((expense) => dayjs(expense.expense_date).format('YYYY-MM') === month)
        .reduce((sum, expense) => sum + Number(expense.amount), 0)
      return {
        month: MONTH_NAMES[monthNum] || monthNum,
        income: Math.round(income * 100) / 100,
        expenses: Math.round(monthExpenses * 100) / 100,
      }
    })
  }, [data])

  const recentPayments = useMemo(() => {
    if (!data?.payments) return []
    return [...data.payments]
      .sort((a, b) => dayjs(b.payment_date).unix() - dayjs(a.payment_date).unix())
      .slice(0, 5)
  }, [data])

  if (isLoading) {
    return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />
  }

  if (isError) {
    return <Typography.Text type="danger">Error al cargar el panel: {(error as Error).message}</Typography.Text>
  }

  const stats = data?.stats

  return (
    <div>
      <Typography.Text
        style={{
          color: 'var(--color-text-secondary)',
          fontSize: 'var(--fs-sm)',
          marginBottom: 24,
          display: 'block',
        }}
      >
        Resumen general de tu cartera inmobiliaria
      </Typography.Text>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {GRADIENT_CARDS.map((card) => (
          <Col key={card.title} xs={24} sm={12} lg={6} className="stagger-card">
            <Card
              style={{
                background: card.gradient,
                border: 'none',
                borderRadius: 'var(--radius-md)',
                boxShadow: card.shadow,
              }}
            >
              <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: 'var(--fs-sm)', marginBottom: 6 }}>
                {card.icon}
                <span style={{ marginLeft: 6 }}>{card.title}</span>
              </div>
              <div style={{ color: '#fff', fontSize: 28, fontWeight: 600, fontFamily: "'DM Sans', sans-serif" }}>
                {card.value(stats)}
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card
            title="Ingresos vs Gastos"
            styles={{
              header: {
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--fs-lg)',
                borderBottom: '1px solid var(--color-border)',
                padding: '16px 20px',
              },
              body: { padding: 20 },
            }}
            style={{
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-sm)',
              height: '100%',
            }}
          >
            {chartData.length > 0 && chartData.some((entry) => entry.income > 0 || entry.expenses > 0) ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} barGap={4} barCategoryGap="20%">
                  <XAxis
                    dataKey="month"
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#7A736C', fontSize: 12, fontFamily: "'DM Sans', sans-serif" }}
                  />
                  <YAxis
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#7A736C', fontSize: 12, fontFamily: "'DM Sans', sans-serif" }}
                    tickFormatter={(value: number) => `${value}€`}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Bar
                    dataKey="income"
                    name="Ingresos"
                    fill="#1A6B6B"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={40}
                  />
                  <Bar
                    dataKey="expenses"
                    name="Gastos"
                    fill="#C1704A"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={40}
                  />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Empty
                description="No hay datos suficientes para mostrar el gráfico"
                style={{ margin: '40px 0' }}
              />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card
            title="Actividad Reciente"
            styles={{
              header: {
                fontFamily: 'var(--font-display)',
                fontSize: 'var(--fs-lg)',
                borderBottom: '1px solid var(--color-border)',
                padding: '16px 20px',
              },
              body: { padding: 20 },
            }}
            style={{
              borderRadius: 'var(--radius-md)',
              boxShadow: 'var(--shadow-sm)',
              height: '100%',
            }}
          >
            {recentPayments.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {recentPayments.map((payment) => (
                  <div
                    key={payment.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 12,
                      paddingBottom: 12,
                      borderBottom: '1px solid var(--color-border)',
                    }}
                  >
                    <div
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        background: 'var(--color-sage)',
                        flexShrink: 0,
                      }}
                    />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontSize: 'var(--fs-sm)',
                          fontWeight: 500,
                          color: 'var(--color-text-primary)',
                        }}
                      >
                        Pago #{payment.id}
                      </div>
                      <div
                        style={{
                          fontSize: 'var(--fs-xs)',
                          color: 'var(--color-text-tertiary)',
                        }}
                      >
                        {dayjs(payment.payment_date).format('D MMM YYYY')}
                      </div>
                    </div>
                    <Tag color="green" style={{ marginRight: 0, borderRadius: 4, fontSize: 'var(--fs-xs)' }}>
                      {fmtMoney(payment.amount)}
                    </Tag>
                  </div>
                ))}
              </div>
            ) : (
              <Empty
                description="Sin actividad reciente"
                style={{ margin: '40px 0' }}
              />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
