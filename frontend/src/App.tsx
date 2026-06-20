import { lazy, Suspense } from 'react'
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

  return (
    <Suspense fallback={fallback}>
      <Routes location={location} key={location.pathname}>
        <Route element={<AppLayout />}>
          <Route path="/" element={
            <div className="page-enter"><Dashboard /></div>
          } />
          <Route path="/leases" element={
            <div className="page-enter"><Leases /></div>
          } />
          <Route path="/leases/:id" element={
            <div className="page-enter"><LeaseDetail /></div>
          } />
          <Route path="/invoices" element={
            <div className="page-enter"><Invoices /></div>
          } />
          <Route path="/payments" element={
            <div className="page-enter"><Payments /></div>
          } />
          <Route path="/expenses" element={
            <div className="page-enter"><Expenses /></div>
          } />
          <Route path="/owners" element={
            <div className="page-enter"><Owners /></div>
          } />
          <Route path="/properties" element={
            <div className="page-enter"><Properties /></div>
          } />
          <Route path="/units" element={
            <div className="page-enter"><Units /></div>
          } />
          <Route path="/tenants" element={
            <div className="page-enter"><Tenants /></div>
          } />
          <Route path="/reconciliation" element={
            <div className="page-enter"><Reconciliation /></div>
          } />
          <Route path="/tutorial" element={
            <div className="page-enter"><Tutorial /></div>
          } />
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
