import { lazy, Suspense } from 'react'
import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
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
const Fiscal = lazy(() => import('./pages/Fiscal'))
const Tutorial = lazy(() => import('./pages/Tutorial'))

const fallback = <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

function page(element: ReactNode) {
  return <div className="page-enter">{element}</div>
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={fallback}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={page(<Dashboard />)} />
            <Route path="/leases" element={page(<Leases />)} />
            <Route path="/leases/:id" element={page(<LeaseDetail />)} />
            <Route path="/invoices" element={page(<Invoices />)} />
            <Route path="/payments" element={page(<Payments />)} />
            <Route path="/expenses" element={page(<Expenses />)} />
            <Route path="/owners" element={page(<Owners />)} />
            <Route path="/properties" element={page(<Properties />)} />
            <Route path="/units" element={page(<Units />)} />
            <Route path="/tenants" element={page(<Tenants />)} />
            <Route path="/reconciliation" element={page(<Reconciliation />)} />
            <Route path="/fiscal" element={page(<Fiscal />)} />
            <Route path="/tutorial" element={page(<Tutorial />)} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
