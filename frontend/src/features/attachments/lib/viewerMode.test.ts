import { describe, expect, it } from 'vitest'
import { decodeText } from './decodeText'
import { blobTypeFor, needsFile, viewerMode } from './viewerMode'

const mode = (name: string, extra: { content_type?: string; preview_source?: 'image' | 'embedded' } = {}) =>
  viewerMode({ name, content_type: extra.content_type ?? null, preview_source: extra.preview_source ?? null })

describe('viewerMode', () => {
  it('muestra de frente lo que el navegador entiende', () => {
    expect(mode('foto.JPG')).toBe('image')
    expect(mode('adjunto', { content_type: 'image/png' })).toBe('image')
    expect(mode('informe.pdf')).toBe('pdf')
    expect(mode('datos.csv')).toBe('text')
    expect(mode('video.mp4')).toBe('video')
    expect(mode('nota.mp3')).toBe('audio')
  })

  it('convierte imágenes no soportadas y usa la miniatura incrustada de planos y Office', () => {
    expect(mode('scan.tif')).toBe('converted')
    expect(mode('logo.emf')).toBe('converted')
    expect(mode('plano.dwg', { preview_source: 'embedded' })).toBe('embedded')
    expect(mode('avance.pptx', { preview_source: 'embedded' })).toBe('embedded')
  })

  it('sin forma de mostrarlo, ofrece descarga', () => {
    expect(mode('plano.dwg')).toBe('none')
    expect(mode('macro.exe')).toBe('none')
    expect(needsFile('none')).toBe(false)
    expect(needsFile('embedded')).toBe(false)
    expect(needsFile('pdf')).toBe(true)
  })

  it('fuerza el tipo MIME sólo donde el navegador lo necesita', () => {
    expect(blobTypeFor('pdf', 'informe')).toBe('application/pdf')
    expect(blobTypeFor('image', 'logo.svg')).toBe('image/svg+xml')
    expect(blobTypeFor('image', 'foto.png')).toBeUndefined()
  })
})

describe('decodeText', () => {
  it('lee UTF-8 y cae a Windows-1252 para archivos con tildes en ANSI', () => {
    expect(decodeText(new TextEncoder().encode('Revisión').buffer)).toBe('Revisión')
    expect(decodeText(new Uint8Array([0x52, 0x65, 0x76, 0x69, 0x73, 0x69, 0xf3, 0x6e]).buffer)).toBe(
      'Revisión',
    )
  })
})

describe('viewerMode por cómo viaja el adjunto', () => {
  it('un correo adjunto y un enlace tienen su propio modo y no piden archivo para verse', () => {
    expect(viewerMode({ name: 'Informe v1.2', kind: 'message' })).toBe('message')
    expect(viewerMode({ name: 'Presupuesto.xlsx', kind: 'link' })).toBe('link')
    expect(viewerMode({ name: 'foto.png', kind: 'file' })).toBe('image')
    expect(needsFile('message')).toBe(false)
    expect(needsFile('link')).toBe(false)
  })
})

describe('viewerMode de calendario y contactos', () => {
  it('muestra .ics, .vcs y .vcf como texto', () => {
    expect(viewerMode({ name: 'invitacion.ics' })).toBe('text')
    expect(viewerMode({ name: 'cita.vcs' })).toBe('text')
    expect(viewerMode({ name: 'ana.vcf' })).toBe('text')
  })
})
