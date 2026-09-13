import { expect, test } from '@playwright/test'

test.describe('Navegación y deep links', () => {
  test('dashboard loads with stats', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Dashboard')).toBeVisible()
    await expect(page.locator('text=Contratos activos')).toBeVisible()
    await expect(page.locator('text=Facturas este mes')).toBeVisible()
    await expect(page.locator('text=Pagos este mes')).toBeVisible()
    await expect(page.locator('text=Gastos este año')).toBeVisible()
  })

  test('deep link to propietarios loads the page', async ({ page }) => {
    await page.goto('/owners')
    await expect(page.getByRole('heading', { name: 'Propietarios' }).first()).toBeVisible()
  })

  test('deep link to conciliación loads the page', async ({ page }) => {
    await page.goto('/reconciliation')
    await expect(page.getByRole('heading', { name: 'Conciliación bancaria' }).first()).toBeVisible()
  })

  test('deep link to fiscal loads the page', async ({ page }) => {
    await page.goto('/fiscal')
    await expect(page.getByRole('heading', { name: 'Informes Fiscales' }).first()).toBeVisible()
    await expect(page.getByRole('tab', { name: 'IVA (303)' })).toBeVisible()
    await expect(page.getByRole('tab', { name: 'Retenciones (190)' })).toBeVisible()
    await expect(page.getByRole('tab', { name: 'Renta (100)' })).toBeVisible()
  })

  test('unknown route redirects to dashboard', async ({ page }) => {
    await page.goto('/ruta-inexistente')
    await expect(page).toHaveURL('/')
  })
})

test.describe('CRUD de propietarios', () => {
  test('create and edit an owner', async ({ page }) => {
    await page.goto('/owners')
    await page.getByRole('button', { name: 'Nuevo propietario' }).click()

    await page.fill('#name', 'E2E Propietario')
    await page.click('#document_type')
    await page.click('.ant-select-item-option:has-text("DNI")')
    await page.fill('#document_number', '99999999Z')
    await page.fill('#email', 'e2e-owner@test.com')
    await page.fill('#phone', '+34 600 000 099')
    await page.getByRole('button', { name: 'Aceptar' }).click()

    await expect(page.locator('text=E2E Propietario')).toBeVisible()

    await page.getByRole('button', { name: 'Editar' }).first().click()
    await page.fill('#name', 'E2E Propietario Editado')
    await page.getByRole('button', { name: 'Aceptar' }).click()

    await expect(page.locator('text=E2E Propietario Editado')).toBeVisible()
  })
})

test.describe('Formularios', () => {
  test('open lease form and cancel', async ({ page }) => {
    await page.goto('/leases')
    await page.getByRole('button', { name: 'Nuevo contrato' }).click()
    await expect(page.getByRole('dialog')).toContainText('Nuevo contrato')
    await page.getByRole('button', { name: 'Cancelar' }).click()
  })

  test('open payment form and cancel', async ({ page }) => {
    await page.goto('/payments')
    await page.getByRole('button', { name: 'Registrar pago' }).click()
    await expect(page.getByRole('dialog')).toContainText('Registrar pago')
    await page.getByRole('button', { name: 'Cancelar' }).click()
  })

  test('open expense form and cancel', async ({ page }) => {
    await page.goto('/expenses')
    await page.getByRole('button', { name: 'Registrar gasto' }).click()
    await expect(page.getByRole('dialog')).toContainText('Registrar gasto')
    await page.getByRole('button', { name: 'Cancelar' }).click()
  })

  test('open invoice generate form and cancel', async ({ page }) => {
    await page.goto('/invoices')
    await page.getByRole('button', { name: 'Generar facturas' }).click()
    await expect(page.getByRole('dialog')).toContainText('Generar facturas')
    await page.getByRole('button', { name: 'Cancelar' }).click()
  })
})
