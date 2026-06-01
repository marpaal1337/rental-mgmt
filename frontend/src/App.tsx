import { lazy, Suspense, useCallback, useRef } from 'react'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import AppLayout from './components/AppLayout'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Leases = lazy(() => import('./pages/Leases'))
const LeaseDetail = lazy(() => import('./pages/LeaseDetail'))
const Invoices = lazy(() => import('./pages/Invoices'))
const Payments = lazy(() => import('./pages/Payments'))
const Expenses = lazy(() => import('./pages/Expenses'))
const Owners = lazy(() => import('./pages/Owners'))
const Properties = lazy(() => import('./pages/Properties'))
const Units = lazy(() => import('./pages/Units'))
const Tenants = lazy(() => import('./pages/Tenants'))
const Reconciliation = lazy(() => import('./pages/Reconciliation'))
const Tutorial = lazy(() => import('./pages/Tutorial'))

const fallback = <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

function AnimatedRoutes() {
  const location = useLocation()
  const nodeRef = useRef<HTMLDivElement>(null)

  const wrapWithTransition = useCallback((element: React.ReactNode) => {
    return <div ref={nodeRef}>{element}</div>
  }, [])

  return (
    <Suspense fallback={fallback}>
      <Routes location={location}>
        <Route element={<AppLayout />}>
          <Route path="/" element={wrapWithTransition(<Dashboard />)} />
          <Route path="/leases" element={wrapWithTransition(<Leases />)} />
          <Route path="/leases/:id" element={wrapWithTransition(<LeaseDetail />)} />
          <Route path="/invoices" element={wrapWithTransition(<Invoices />)} />
          <Route path="/payments" element={wrapWithTransition(<Payments />)} />
          <Route path="/expenses" element={wrapWithTransition(<Expenses />)} />
          <Route path="/owners" element={wrapWithTransition(<Owners />)} />
          <Route path="/properties" element={wrapWithTransition(<Properties />)} />
          <Route path="/units" element={wrapWithTransition(<Units />)} />
          <Route path="/tenants" element={wrapWithTransition(<Tenants />)} />
          <Route path="/reconciliation" element={wrapWithTransition(<Reconciliation />)} />
          <Route path="/tutorial" element={wrapWithTransition(<Tutorial />)} />
        </Route>
      </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AnimatedRoutes />
    </BrowserRouter>
  )
}
