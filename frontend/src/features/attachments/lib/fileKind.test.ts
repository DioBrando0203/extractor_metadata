import { describe, expect, it } from 'vitest'
import { fileKind, kindLabel } from './fileKind'

describe('fileKind', () => {
  it('prioriza la extensión del nombre', () => {
    expect(fileKind('plano.DWG', 'application/octet-stream')).toBe('cad')
    expect(fileKind('informe.xlsx')).toBe('excel')
    expect(fileKind('image001.png', 'application/pdf')).toBe('image')
  })

  it('usa el tipo MIME cuando el nombre no tiene extensión', () => {
    expect(fileKind('adjunto', 'application/pdf')).toBe('pdf')
    expect(
      fileKind('adjunto', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
    ).toBe('word')
    expect(fileKind('adjunto', null)).toBe('other')
  })
})

describe('kindLabel', () => {
  it('muestra la extensión o una descripción genérica', () => {
    expect(kindLabel('acta.pdf')).toBe('PDF')
    expect(kindLabel('adjunto', 'image/png')).toBe('Imagen')
    expect(kindLabel('adjunto')).toBe('Archivo')
  })
})
