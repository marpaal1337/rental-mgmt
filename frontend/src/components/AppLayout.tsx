import { useMemo } from 'react'
import {
  AuditOutlined, BankOutlined, BookOutlined, DashboardOutlined,
  FileTextOutlined, HomeOutlined, MoneyCollectOutlined, TeamOutlined,
  ShopOutlined, AppstoreOutlined, UserOutlined, ReconciliationOutlined,
} from '@ant-design/icons'
import { Layout, Menu } from 'antd'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'

const { Sider, Content } = Layout

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: 'Dashboard' },
  { key: '/tutorial', icon: <BookOutlined />, label: 'Tutorial' },
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

const pageTitles: Record<string, string> = {
  '/': 'Panel de Control',
  '/tutorial': 'Tutorial',
  '/leases': 'Contratos',
  '/invoices': 'Facturas',
  '/payments': 'Pagos',
  '/expenses': 'Gastos',
  '/owners': 'Propietarios',
  '/tenants': 'Inquilinos',
  '/properties': 'Propiedades',
  '/units': 'Unidades',
  '/reconciliation': 'Conciliación',
}

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()

  const selectedKey = useMemo(() => {
    const path = location.pathname
    if (path.startsWith('/leases/')) return '/leases'
    return path
  }, [location.pathname])

  const pageTitle = useMemo(() => {
    const path = location.pathname
    if (path.startsWith('/leases/')) return 'Detalle del Contrato'
    return pageTitles[path] ?? 'Rental Management'
  }, [location.pathname])

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        width={240}
        breakpoint="lg"
        collapsedWidth={64}
        style={{
          background: 'linear-gradient(180deg, #142828 0%, #0D1E1E 100%)',
          borderRight: '1px solid rgba(255,255,255,0.06)',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          zIndex: 100,
          overflow: 'auto',
        }}
      >
        <div
          style={{
            height: 72,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            padding: '0 16px',
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #1A6B6B 0%, #248A8A 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <HomeOutlined style={{ fontSize: 18, color: '#fff' }} />
          </div>
          <span
            style={{
              fontFamily: "'DM Serif Display', Georgia, serif",
              fontSize: 18,
              color: '#fff',
              letterSpacing: '0.02em',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            Hacienda
          </span>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          defaultOpenKeys={['master']}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{
            background: 'transparent',
            borderRight: 'none',
            paddingTop: 8,
          }}
        />
      </Sider>
      <Layout style={{ marginLeft: 240 }}>
        <div
          style={{
            height: 72,
            padding: '0 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#FFFFFF',
            borderBottom: '1px solid var(--color-border)',
            position: 'sticky',
            top: 0,
            zIndex: 50,
          }}
        >
          <h1
            style={{
              fontFamily: "'DM Serif Display', Georgia, serif",
              fontSize: 22,
              fontWeight: 400,
              color: 'var(--color-text-primary)',
              margin: 0,
            }}
          >
            {pageTitle}
          </h1>
          <div
            style={{
              fontSize: 'var(--fs-sm)',
              color: 'var(--color-text-tertiary)',
              fontFamily: "'DM Sans', sans-serif",
            }}
          >
            Gestión Inmobiliaria
          </div>
        </div>
        <Content
          style={{
            margin: 0,
            padding: 28,
            minHeight: 'calc(100vh - 72px)',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
