import { describe, expect, it } from 'vitest'
import { attachmentMeta, describeAttachment, fileKind, kindLabel } from './fileKind'

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

describe('describeAttachment y attachmentMeta', () => {
  it('un correo adjunto es Correo aunque su asunto parezca tener extensión', () => {
    expect(describeAttachment({ name: 'Informe v1.2', kind: 'message' })).toEqual({
      kind: 'mail',
      label: 'Correo',
    })
    expect(attachmentMeta({ name: 'Informe v1.2', kind: 'message', size_bytes: 2048 })).toBe('Correo · 2 KB')
  })

  it('un enlace muestra su tipo y dónde vive en lugar del tamaño', () => {
    const cloud = {
      name: 'Presupuesto.xlsx',
      kind: 'link' as const,
      link: 'https://contoso.sharepoint.com/x',
    }
    expect(describeAttachment(cloud).kind).toBe('excel')
    expect(attachmentMeta(cloud)).toBe('XLSX · Enlace web')
    const share = String.raw`\\servidor\obras\Presupuesto.xlsx`
    expect(attachmentMeta({ ...cloud, link: share })).toBe('XLSX · Carpeta compartida')
  })
})
