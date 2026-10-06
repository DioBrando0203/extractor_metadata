import { describe, expect, it } from 'vitest'
import { findRanges, normalizeText, searchTerms, snippetAround } from './textSearch'

describe('textSearch', () => {
  it('normaliza tildes y mayúsculas y deduplica términos', () => {
    expect(normalizeText('Revisión ÁRBOL')).toBe('revision arbol')
    expect(searchTerms('  Plano  plano REVISIÓN ')).toEqual(['plano', 'revision'])
  })

  it('devuelve rangos sobre el texto original aunque tenga tildes', () => {
    const text = 'La revisión del plano'
    const ranges = findRanges(text, ['revision', 'plano'])
    expect(ranges.map((range) => text.slice(range.start, range.end))).toEqual(['revisión', 'plano'])
  })

  it('une coincidencias solapadas y encuentra direcciones de correo', () => {
    const text = 'Para: ana@example.test'
    const [range] = findRanges(text, ['ana@', '@example'])
    expect(text.slice(range.start, range.end)).toBe('ana@example')
    expect(findRanges('sin nada', ['plano'])).toEqual([])
  })

  it('arma un fragmento alrededor de la primera coincidencia', () => {
    const text = `${'x '.repeat(80)}Martin County ${'y '.repeat(80)}`
    const snippet = snippetAround(text, ['martin'], 10)
    expect(snippet?.startsWith('…')).toBe(true)
    expect(snippet).toContain('Martin County')
    expect(snippetAround('nada aquí', ['plano'])).toBeNull()
  })
})
