import { describe, expect, it } from 'vitest'
import { isWebLink, splitLinks } from './links'

describe('splitLinks', () => {
  it('separa las direcciones web sin cambiar el texto', () => {
    const text = 'Revisa el informe <https://contoso.example.test/informe?id=7>. Gracias.'
    const segments = splitLinks(text)
    expect(segments.map((segment) => segment.text).join('')).toBe(text)
    expect(segments.filter((segment) => segment.link).map((segment) => segment.link)).toEqual([
      'https://contoso.example.test/informe?id=7',
    ])
  })

  it('no toma la puntuación final ni esquemas que no son web', () => {
    expect(splitLinks('Ver http://intranet.example.test/acta.pdf, por favor.')[1]).toEqual({
      text: 'http://intranet.example.test/acta.pdf',
      link: 'http://intranet.example.test/acta.pdf',
    })
    expect(splitLinks('javascript:alert(1) y file:///C:/x').every((segment) => !segment.link)).toBe(true)
    expect(splitLinks('sin enlaces')).toEqual([{ text: 'sin enlaces' }])
  })

  it('reconoce sólo http y https como enlace', () => {
    expect(isWebLink('https://a.example.test')).toBe(true)
    expect(isWebLink('https://')).toBe(false)
  })
})
