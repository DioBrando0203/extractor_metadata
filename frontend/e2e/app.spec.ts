import { expect, test } from '@playwright/test'

test('muestra el punto de entrada y la ayuda en escritorio', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Cargar MSG' })).toBeVisible()
  await page.getByRole('button', { name: 'Ayuda' }).click()
  await expect(page.getByRole('heading', { name: 'Cómo analizar un MSG' })).toBeVisible()
})
