import { expect, test } from '@playwright/test'

test.describe('Rental Management E2E', () => {
  test('dashboard loads with stats', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Dashboard')).toBeVisible()
    await expect(page.locator('text=Contratos activos')).toBeVisible()
    await expect(page.locator('text=Facturas este mes')).toBeVisible()
    await expect(page.locator('text=Pagos este mes')).toBeVisible()
    await expect(page.locator('text=Gastos este año')).toBeVisible()
  })

  test('navigate to contratos', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Contratos')
    await expect(page).toHaveURL('/leases')
    await expect(page.locator('text=Nuevo')).toBeVisible()
  })

  test('navigate to facturas', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Facturas')
    await expect(page).toHaveURL('/invoices')
    await expect(page.locator('text=Generar')).toBeVisible()
  })

  test('navigate to pagos', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Pagos')
    await expect(page).toHaveURL('/payments')
    await expect(page.locator('text=Registrar')).toBeVisible()
  })

  test('navigate to gastos', async ({ page }) => {
    await page.goto('/')
    await page.click('text=Gastos')
    await expect(page).toHaveURL('/expenses')
    await expect(page.locator('text=Registrar')).toBeVisible()
  })

  test('open lease form and cancel', async ({ page }) => {
    await page.goto('/leases')
    await page.click('text=Nuevo')
    await expect(page.locator('text=Nuevo contrato')).toBeVisible()
    await page.click('button:has-text("Cancel")')
  })

  test('open payment form and cancel', async ({ page }) => {
    await page.goto('/payments')
    await page.click('text=Registrar')
    await expect(page.locator('text=Registrar pago')).toBeVisible()
    await page.click('button:has-text("Cancel")')
  })

  test('open expense form and cancel', async ({ page }) => {
    await page.goto('/expenses')
    await page.click('text=Registrar')
    await expect(page.locator('text=Registrar gasto')).toBeVisible()
    await page.click('button:has-text("Cancel")')
  })

  test('open invoice generate form and cancel', async ({ page }) => {
    await page.goto('/invoices')
    await page.click('text=Generar')
    await expect(page.locator('text=Generar facturas')).toBeVisible()
    await page.click('button:has-text("Cancel")')
  })
})
