import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

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

const attachment = (name: string, size_bytes: number, content_type: string | null = null) => ({
  name,
  content_type,
  size_bytes,
  metadata: [],
  warnings: [],
})

const complete = {
  file_name: 'Revision planos.msg',
  file_size_bytes: 4_812_331,
  subject: 'RE: Proyecto 24-123 | Revisión de planos estructurales y memoria de cálculo actualizada',
  sender: 'María Fernández <maria.fernandez@example.test>',
  recipients: [
    `Para: ${Array.from({ length: 12 }, (_, i) => `Persona ${i + 1} <persona${i + 1}@example.test>`).join('; ')}`,
    'CC: Lucía Torres <lucia.torres@example.test>; Jorge Medina <jorge.medina@example.test>',
  ],
  sent_at: '2026-10-05T15:42:00-05:00',
  body_preview:
    'Hola equipo,\r\n\r\nAdjunto la revisión 3 de los planos y la memoria de cálculo actualizada. Los cambios principales están en las láminas S-201 a S-204.\r\n\r\n\r\n\r\nSaludos,\r\nMaría',
  body_truncated: true,
  status: 'complete',
  headers: [],
  properties: [],
  attachments: [
    attachment('S-201 Vigas eje C rev3.pdf', 1_245_000),
    attachment('Modelo estructural.dwg', 2_310_442),
    attachment('Memoria de cálculo v3.docx', 412_330),
    attachment('Metrado acero.xlsx', 88_120),
    attachment('image001.png', 14_220),
    attachment('Presentación avance.pptx', 3_120_000),
    attachment('Fotos obra.zip', 5_400_000),
    attachment('adjunto', 2048, 'application/pdf'),
  ],
  warnings: [],
}

const partial = {
  ...complete,
  file_name: 'RE_ Proyecto 24-123 _ Archivo con nombre muy largo guardado desde el cliente de correo.msg',
  subject: null,
  sender: null,
  recipients: [],
  sent_at: null,
  body_truncated: false,
  status: 'partial',
}

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
    const message = body.includes('RE_ Proyecto') ? partial : complete
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message, processed_locally: true }),
    })
  })
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

const FILES = [
  'Revision planos.msg',
  'RE_ Proyecto 24-123 _ Archivo con nombre muy largo guardado desde el cliente de correo.msg',
  'falla.msg',
  'lento.msg',
]

for (const viewport of WIDTHS) {
  test(`capturas a ${viewport.width}px`, { tag: '@visual' }, async ({ page }) => {
    const narrow = viewport.width <= 860
    await page.setViewportSize(viewport)

    await open(page, [])
    await capture(page, '01-portada')

    await open(page, FILES)
    await page.getByRole('heading', { name: /Revisión de planos/ }).waitFor()
    await capture(page, '02-correo')

    const select = async (name: RegExp) => {
      if (narrow) await page.getByRole('button', { name: /^Bandeja \(/ }).click()
      await page.getByRole('button', { name }).click()
    }
    if (narrow) {
      await page.getByRole('button', { name: /^Bandeja \(/ }).click()
      await capture(page, '03-bandeja')
      await page.getByRole('button', { name: /Revisión de planos/ }).click()
    }
    await select(/Remitente desconocido/)
    await capture(page, '04-parcial')
    await select(/^falla/)
    await capture(page, '05-error')
    await select(/^lento/)
    await capture(page, '06-cargando')
    await page.getByRole('button', { name: 'Ayuda', exact: true }).click()
    await capture(page, '07-ayuda')
  })
}
