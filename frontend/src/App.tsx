import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
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

const fallback = <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={fallback}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/leases" element={<Leases />} />
            <Route path="/leases/:id" element={<LeaseDetail />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/expenses" element={<Expenses />} />
            <Route path="/owners" element={<Owners />} />
            <Route path="/properties" element={<Properties />} />
            <Route path="/units" element={<Units />} />
            <Route path="/tenants" element={<Tenants />} />
            <Route path="/reconciliation" element={<Reconciliation />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
