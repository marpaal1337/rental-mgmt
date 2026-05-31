import { FileTextOutlined, HomeOutlined, MoneyCollectOutlined, ShoppingCartOutlined } from '@ant-design/icons'
import { Card, Col, Row, Spin, Statistic, Typography } from 'antd'
import { useEffect, useState } from 'react'
import { fetchStats } from '../api/endpoints'
import type { DashboardStats } from '../types'

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

  return (
    <>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Contratos activos"
              value={stats?.active_leases ?? 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Facturas este mes"
              value={stats?.month_invoices ?? 0}
              prefix={<ShoppingCartOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Pagos este mes"
              value={stats?.month_payments ?? 0}
              prefix={<MoneyCollectOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Gastos este año"
              value={stats?.year_expenses ?? 0}
              prefix={<HomeOutlined />}
            />
          </Card>
        </Col>
      </Row>
    </>
  )
}
