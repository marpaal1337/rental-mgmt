import {
  AuditOutlined,
  BankOutlined,
  DashboardOutlined,
  FileTextOutlined,
  HomeOutlined,
  MoneyCollectOutlined,
  TeamOutlined,
  ShopOutlined,
  AppstoreOutlined,
  UserOutlined,
  ReconciliationOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Typography } from 'antd'
import { Outlet, useNavigate } from 'react-router-dom'

const { Sider, Content, Header } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/leases', icon: <FileTextOutlined />, label: 'Contratos' },
  { key: '/invoices', icon: <AuditOutlined />, label: 'Facturas' },
  { key: '/payments', icon: <MoneyCollectOutlined />, label: 'Pagos' },
  { key: '/expenses', icon: <BankOutlined />, label: 'Gastos' },
  {
    key: 'master',
    icon: <TeamOutlined />,
    label: 'Maestros',
    children: [
      { key: '/owners', icon: <UserOutlined />, label: 'Propietarios' },
      { key: '/tenants', icon: <TeamOutlined />, label: 'Inquilinos' },
      { key: '/properties', icon: <ShopOutlined />, label: 'Propiedades' },
      { key: '/units', icon: <AppstoreOutlined />, label: 'Unidades' },
    ],
  },
  { key: '/reconciliation', icon: <ReconciliationOutlined />, label: 'Conciliación' },
]

export default function AppLayout() {
  const navigate = useNavigate()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        theme="dark"
        breakpoint="lg"
        collapsedWidth={64}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <HomeOutlined style={{ fontSize: 28, color: '#fff' }} />
        </div>
        <Menu
          theme="dark"
          mode="inline"
          defaultSelectedKeys={['/']}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Typography.Title level={4} style={{ margin: 0 }}>
            Rental Management
          </Typography.Title>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
