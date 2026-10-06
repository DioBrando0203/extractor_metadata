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
