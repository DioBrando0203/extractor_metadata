import { describe, expect, it } from 'vitest'
import { isWebLink, linkPlace } from './link'

describe('isWebLink', () => {
  it('sólo http y https se pueden abrir como enlace', () => {
    expect(isWebLink('https://contoso.sharepoint.com/:x:/r/sites/obra/Presupuesto.xlsx')).toBe(true)
    expect(isWebLink('http://intranet.example.test/acta.pdf')).toBe(true)
    expect(isWebLink(String.raw`\\servidor\obras\plano.dwg`)).toBe(false)
    expect(isWebLink('file:///C:/obras/plano.dwg')).toBe(false)
    expect(isWebLink('javascript:alert(1)')).toBe(false)
    expect(isWebLink(null)).toBe(false)
  })
})

describe('linkPlace', () => {
  it('describe dónde vive el archivo', () => {
    expect(linkPlace('https://onedrive.example.test/x')).toBe('Enlace web')
    expect(linkPlace(String.raw`\\servidor\obras\plano.dwg`)).toBe('Carpeta compartida')
    expect(linkPlace(undefined)).toBe('Enlace sin dirección')
  })
})
