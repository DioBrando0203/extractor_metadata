import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'
import { COMPLETE, PARTIAL, PHOTO } from './visual-fixtures'

/*
 * Revisión visual (regla C-07): capturas en test-results/capturas/ con respuestas simuladas y
 * datos sintéticos. Se ejecuta con `npm run test:visual`; `npm run test:e2e` la excluye.
 */

const OUT = 'test-results/capturas'
const WIDTHS = [
  { width: 320, height: 700 },
  { width: 390, height: 844 },
  { width: 1024, height: 768 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
]
const FILES = [
  'Revision planos.msg',
  'RE_ Proyecto 24-123 _ Archivo con nombre muy largo guardado desde el cliente de correo.msg',
  'falla.msg',
  'lento.msg',
]

async function open(page: Page, files: string[]) {
  await page.route('**/api/messages/extract', async (route) => {
    const body = route.request().postDataBuffer()?.toString('latin1') ?? ''
    if (body.includes('falla.msg')) {
      return route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'El archivo no tiene una firma MSG/OLE válida.' }),
      })
    }
    if (body.includes('lento.msg')) return // sin respuesta: queda en lectura
    const message = body.includes('RE_ Proyecto') ? PARTIAL : COMPLETE
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message, processed_locally: true }),
    })
  })
  await page.route('**/api/messages/attachment', (route) =>
    route.fulfill({ status: 200, contentType: 'image/png', body: PHOTO }),
  )
  await page.goto('/')
  if (files.length) {
    await page
      .locator('input[type=file]')
      .first()
      .setInputFiles(
        files.map((name) => ({ name, mimeType: 'application/vnd.ms-outlook', buffer: Buffer.from('x') })),
      )
  }
}

async function capture(page: Page, name: string) {
  await page.waitForTimeout(300)
  const width = page.viewportSize()?.width
  await page.screenshot({ path: `${OUT}/${width}-${name}.png` })
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow, `${name} a ${width}px no debe desbordar`).toBeLessThanOrEqual(0)
}

for (const viewport of WIDTHS) {
  test(`capturas a ${viewport.width}px`, { tag: '@visual' }, async ({ page }) => {
    const narrow = viewport.width <= 860
    await page.setViewportSize(viewport)

    await open(page, [])
    await capture(page, '01-portada')

    await open(page, FILES)
    await page.getByRole('heading', { name: /Revisión de planos/ }).waitFor()
    await capture(page, '02-correo')

    await page.getByRole('button', { name: 'Ver Foto obra frontal.png' }).click()
    await page.getByRole('dialog').getByRole('img').waitFor()
    await capture(page, '03-visor-imagen')
    await page.getByRole('button', { name: 'Adjunto siguiente' }).click()
    await page.getByRole('button', { name: /Detalles/ }).click()
    await capture(page, '04-visor-plano')
    await page.keyboard.press('Escape')

    const select = async (name: RegExp) => {
      if (narrow) await page.getByRole('button', { name: /^Bandeja \(/ }).click()
      await page.getByRole('button', { name }).click()
    }
    if (narrow) {
      await page.getByRole('button', { name: /^Bandeja \(/ }).click()
      await capture(page, '05-bandeja')
      await page.getByRole('button', { name: /Revisión de planos/ }).click()
    }
    await select(/Remitente desconocido/)
    await capture(page, '06-parcial')
    await select(/^falla/)
    await capture(page, '07-error')
    await select(/^lento/)
    await capture(page, '08-cargando')
    await page.getByRole('searchbox').fill('memoria')
    await capture(page, '09-busqueda')
    await page.getByRole('button', { name: 'Ayuda', exact: true }).click()
    await capture(page, '10-ayuda')
  })
}
