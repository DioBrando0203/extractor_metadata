import { execFileSync } from 'node:child_process'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const backend = resolve('..', 'backend')
const python = resolve(backend, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
function fixture() {
  return execFileSync(
    python,
    [
      '-c',
      "import sys; sys.path.insert(0,'tests'); from msg_factory import make_msg; sys.stdout.buffer.write(make_msg(attachment=b'AC1032' + b'0'*64,filename='plano.dwg'))",
    ],
    { cwd: backend },
  )
}

test('cola real: un MSG corrupto no impide inspeccionar y exportar el siguiente', async ({
  page,
}, testInfo) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await page
    .locator('input[type=file]')
    .first()
    .setInputFiles([
      { name: 'roto.msg', mimeType: 'application/vnd.ms-outlook', buffer: Buffer.from('MSG corrupto') },
      { name: 'correcto.msg', mimeType: 'application/vnd.ms-outlook', buffer: fixture() },
    ])
  const correct = page.getByRole('button', { name: /Mensaje de prueba — áéíóú/ })
  await expect(correct).toBeVisible({ timeout: 20_000 })
  await correct.click()
  await expect(page.getByRole('heading', { name: 'Mensaje de prueba — áéíóú' })).toBeVisible()
  await page.getByRole('tab', { name: 'Cuerpo', exact: true }).click()
  await expect(page.getByRole('tabpanel')).toContainText('Contenido de prueba local.')
  await page.getByRole('tab', { name: 'Encabezados', exact: true }).click()
  await expect(page.getByRole('tabpanel')).toContainText('Message-ID')
  await page.getByRole('tab', { name: /Adjuntos/ }).click()
  await page.locator('details summary').click()
  await expect(page.getByRole('tabpanel')).toContainText('Firma DWG')
  await expect(page.getByRole('tabpanel')).toContainText('AC1032')
  await page.screenshot({ path: testInfo.outputPath('desktop-adjuntos.png'), fullPage: true })
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Exportar informe JSON' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('correcto-metadata.json')
  const downloadedPath = await download.path()
  expect(downloadedPath).not.toBeNull()
  const report = JSON.parse(await readFile(downloadedPath!, 'utf8'))
  expect(report.message.subject).toBe('Mensaje de prueba — áéíóú')
  expect(report.message.attachments[0].name).toBe('plano.dwg')
  await page.getByRole('button', { name: 'Limpiar sesión' }).click()
  await expect(page.getByRole('heading', { name: 'Lee lo que Outlook no pudo' })).toBeVisible()
  expect(errors).toEqual([])
})

for (const viewportWidth of [320, 390]) {
  test(`en móvil a ${viewportWidth}px se eligen resultados sin desbordar el ancho`, async ({
    page,
  }, testInfo) => {
    await page.setViewportSize({ width: viewportWidth, height: 844 })
    await page.goto('/')
    await page
      .locator('input[type=file]')
      .first()
      .setInputFiles([
        { name: 'primero.msg', mimeType: 'application/vnd.ms-outlook', buffer: fixture() },
        { name: 'segundo.msg', mimeType: 'application/vnd.ms-outlook', buffer: fixture() },
      ])
    const results = page.getByRole('button', { name: /Mensaje de prueba — áéíóú/ })
    await expect(results).toHaveCount(2, { timeout: 20_000 })
    await results.nth(1).click()
    await expect(page.getByRole('heading', { name: 'Mensaje de prueba — áéíóú' })).toBeVisible()
    await expect(page.getByText('segundo.msg', { exact: true })).toBeVisible()
    const width = await page.evaluate(() => ({
      scroll: document.documentElement.scrollWidth,
      client: document.documentElement.clientWidth,
    }))
    expect(width.scroll).toBeLessThanOrEqual(width.client)
    await page.screenshot({ path: testInfo.outputPath('mobile-lector.png'), fullPage: true })
  })
}

test('el arranque unificado sirve el build y extrae un MSG desde el mismo origen', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000')
  await expect(page.getByRole('heading', { name: 'Lee lo que Outlook no pudo' })).toBeVisible()
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'produccion.msg',
    mimeType: 'application/vnd.ms-outlook',
    buffer: fixture(),
  })
  await expect(page.getByRole('heading', { name: 'Mensaje de prueba — áéíóú' })).toBeVisible({
    timeout: 20_000,
  })
})
