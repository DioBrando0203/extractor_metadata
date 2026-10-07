import { execFileSync } from 'node:child_process'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { expect, test } from '@playwright/test'

const backend = resolve('..', 'backend')
const interpreter = resolve(
  backend,
  '.venv',
  process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python',
)

function python(code: string) {
  return execFileSync(interpreter, ['-c', `import sys; sys.path.insert(0,'tests'); ${code}`], {
    cwd: backend,
  })
}

function fixture() {
  return python(
    "from msg_factory import make_msg; sys.stdout.buffer.write(make_msg(attachment=b'AC1032' + b'0'*64,filename='plano.dwg'))",
  )
}

function photoFixture() {
  return python(
    "import io; from PIL import Image; from msg_factory import make_msg; b=io.BytesIO(); Image.new('RGB',(320,200),(30,120,200)).save(b,'PNG'); sys.stdout.buffer.write(make_msg(attachment=b.getvalue(),filename='foto.png'))",
  )
}

/** Correo que reenvía otro como adjunto (con un PDF dentro) y enlaza un archivo de la nube. */
function forwardedFixture() {
  return python(
    [
      'from msg_factory import build_cfb, message_streams, attached_message, reference_attachment',
      "inner = message_streams(subject='Cotización interna', sender='proveedor@example.test', body='Texto del correo reenviado.', attachment=b'%PDF-1.4 cotizacion %%EOF', filename='informe.pdf')",
      "streams = attached_message('__attach_version1.0_#00000000', inner, 'Cotización interna')",
      "streams.update(reference_attachment('__attach_version1.0_#00000001', 'Presupuesto.xlsx', 'https://contoso.example.test/Presupuesto.xlsx'))",
      "sys.stdout.buffer.write(build_cfb(message_streams(subject='Reenvío de cotización', body='Te reenvío el correo.', extra_streams=streams)))",
    ].join('; '),
  )
}

test('un correo adjunto se lee como un correo propio y su PDF se descarga', async ({ page }) => {
  await page.goto('/')
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'reenvio.msg',
    mimeType: 'application/vnd.ms-outlook',
    buffer: forwardedFixture(),
  })
  await expect(page.getByRole('heading', { name: 'Reenvío de cotización' })).toBeVisible({ timeout: 20_000 })
  await expect(page.getByText('XLSX · Enlace web')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Descargar Presupuesto.xlsx' })).toHaveCount(0)

  await page.getByRole('button', { name: 'Abrir Cotización interna' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Cotización interna' })).toBeFocused()
  await expect(page.getByText('proveedor@example.test')).toBeVisible()
  await expect(page.getByText('Texto del correo reenviado.')).toBeVisible()
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Descargar informe.pdf' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('informe.pdf')
  const downloadedPath = await download.path()
  expect(downloadedPath).not.toBeNull()
  expect((await readFile(downloadedPath!)).toString()).toBe('%PDF-1.4 cotizacion %%EOF')

  await page.getByRole('button', { name: 'Volver a Reenvío de cotización' }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Reenvío de cotización' })).toBeFocused()
})

/** Convocatoria de reunión con inicio, fin y lugar como propiedades con nombre de Outlook. */
function meetingFixture() {
  return python(
    [
      'import struct',
      'from datetime import datetime, timezone',
      'from msg_factory import make_msg',
      "A = '{00062002-0000-0000-C000-000000000046}'",
      "ft = lambda d: struct.pack('<Q', int((d - datetime(1601, 1, 1, tzinfo=timezone.utc)).total_seconds() * 10000000))",
      's = datetime(2026, 10, 12, 15, 0, tzinfo=timezone.utc)',
      'e = datetime(2026, 10, 12, 16, 30, tzinfo=timezone.utc)',
      "named = ((A, 0x820D, '0040', ft(s)), (A, 0x820E, '0040', ft(e)), (A, 0x8208, '001F', 'Sala Pacífico'.encode('utf-16-le')))",
      "sys.stdout.buffer.write(make_msg(subject='Revisión de planos', message_class='IPM.Schedule.Meeting.Request', named=named))",
    ].join('; '),
  )
}

test('una convocatoria muestra cuándo y dónde es la reunión', async ({ page }) => {
  await page.goto('/')
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'reunion.msg',
    mimeType: 'application/vnd.ms-outlook',
    buffer: meetingFixture(),
  })
  const card = page.getByRole('region', { name: 'Invitación a una reunión' })
  await expect(card).toBeVisible({ timeout: 20_000 })
  await expect(card.getByText('Sala Pacífico')).toBeVisible()
  await expect(card.getByText(/12 de octubre de 2026, \d\d:\d\d – \d\d:\d\d/)).toBeVisible()
})

test('un correo firmado muestra su contenido y sus adjuntos reales', async ({ page }) => {
  const signed = python(
    "from test_smime import _clear_signed, _smime_msg; sys.stdout.buffer.write(_smime_msg('IPM.Note.SMIME.MultipartSigned', _clear_signed()))",
  )
  await page.goto('/')
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'firmado.msg',
    mimeType: 'application/vnd.ms-outlook',
    buffer: signed,
  })
  await expect(page.getByText('Firmado digitalmente.')).toBeVisible({ timeout: 20_000 })
  await expect(
    page.getByRole('region', { name: 'Contenido del correo' }).getByText('Texto firmado del contrato.'),
  ).toBeVisible()
  await expect(page.getByRole('button', { name: 'Ver smime.p7m' })).toHaveCount(0)
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Descargar contrato.pdf' }).click()
  const download = await downloadPromise
  const downloadedPath = await download.path()
  expect(downloadedPath).not.toBeNull()
  expect((await readFile(downloadedPath!)).toString()).toContain('contrato firmado')
})

test('descargar todo entrega un ZIP con los adjuntos que traen bytes', async ({ page }) => {
  await page.goto('/')
  await page
    .locator('input[type=file]')
    .first()
    .setInputFiles({
      name: 'obra.msg',
      mimeType: 'application/vnd.ms-outlook',
      buffer: python('from test_archive import _mail; sys.stdout.buffer.write(_mail())'),
    })
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Descargar todo' }).click({ timeout: 20_000 })
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('obra - adjuntos.zip')
  const zip = await readFile((await download.path())!)
  expect(zip.subarray(0, 2).toString()).toBe('PK')
  for (const name of ['informe.pdf', 'Informe (2).pdf', 'Pedido.msg']) expect(zip.includes(name)).toBe(true)
  expect(zip.includes('Presupuesto.xlsx')).toBe(false)
})

test('un correo legible permite descargar su adjunto', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'correcto.msg',
    mimeType: 'application/vnd.ms-outlook',
    buffer: fixture(),
  })
  await expect(page.getByRole('heading', { name: /Mensaje de prueba/ })).toBeVisible({ timeout: 20_000 })
  await expect(page.getByText('Observaciones del extractor')).toHaveCount(0)
  await expect(page.getByRole('tab')).toHaveCount(0)
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Descargar' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toBe('plano.dwg')
  const downloadedPath = await download.path()
  expect(downloadedPath).not.toBeNull()
  expect((await readFile(downloadedPath!)).subarray(0, 6).toString()).toBe('AC1032')
  expect(errors).toEqual([])
})

for (const viewportWidth of [320, 390]) {
  test(`en movil a ${viewportWidth}px se muestran las acciones sin desborde`, async ({ page }) => {
    await page.setViewportSize({ width: viewportWidth, height: 844 })
    await page.goto('/')
    await page.locator('input[type=file]').first().setInputFiles({
      name: 'movil.msg',
      mimeType: 'application/vnd.ms-outlook',
      buffer: fixture(),
    })
    await expect(page.getByRole('heading', { name: /Mensaje de prueba/ })).toBeVisible({ timeout: 20_000 })
    await expect(page.getByRole('button', { name: 'Descargar' })).toBeVisible()
    // Maestro-detalle: volver a la bandeja y reabrir el correo desde la lista.
    await page.getByRole('button', { name: /^Bandeja \(1\)/ }).click()
    await expect(page.getByRole('complementary', { name: 'Bandeja de correos' })).toBeVisible()
    await expect(page.getByRole('heading', { name: /Mensaje de prueba/ })).toBeHidden()
    await page.getByRole('button', { name: /Mensaje de prueba/ }).click()
    await expect(page.getByRole('heading', { name: /Mensaje de prueba/ })).toBeVisible()
    const width = await page.evaluate(() => ({
      scroll: document.documentElement.scrollWidth,
      client: document.documentElement.clientWidth,
    }))
    expect(width.scroll).toBeLessThanOrEqual(width.client)
  })
}

test('una imagen adjunta se ve en miniatura y se abre de frente en el visor', async ({ page }) => {
  await page.goto('/')
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'foto.msg',
    mimeType: 'application/vnd.ms-outlook',
    buffer: photoFixture(),
  })
  const card = page.getByRole('button', { name: 'Ver foto.png' })
  await expect(card.locator('img')).toHaveAttribute('src', /^data:image\/jpeg;base64,/, { timeout: 20_000 })
  await card.click()
  const viewer = page.getByRole('dialog', { name: 'foto.png' })
  const image = viewer.getByRole('img', { name: 'foto.png' })
  await expect(image).toBeVisible()
  expect(await image.evaluate((element: HTMLImageElement) => element.naturalWidth)).toBe(320)
  await page.keyboard.press('Escape')
  await expect(viewer).toHaveCount(0)
  await expect(card).toBeFocused()
})

test('el backend sirve el build y extrae un MSG desde el mismo origen', async ({ page }) => {
  await page.goto('http://127.0.0.1:8000')
  await page.locator('input[type=file]').first().setInputFiles({
    name: 'produccion.msg',
    mimeType: 'application/vnd.ms-outlook',
    buffer: fixture(),
  })
  await expect(page.getByRole('heading', { name: /Mensaje de prueba/ })).toBeVisible({ timeout: 20_000 })
})
