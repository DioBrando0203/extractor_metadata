/**
 * Búsqueda de texto sin distinguir mayúsculas ni tildes, con posiciones en el texto original para
 * resaltar coincidencias. Funciones puras compartidas por la bandeja y el lector.
 */

export interface TextRange {
  start: number
  end: number
}

const COMBINING_MARKS = /\p{M}/gu

/** Minúsculas y sin tildes: "Revisión" coincide con "revision". */
export function normalizeText(text: string): string {
  return text.normalize('NFD').replace(COMBINING_MARKS, '').toLowerCase()
}

/** Palabras de búsqueda normalizadas y sin repetir. */
export function searchTerms(query: string): string[] {
  return [...new Set(normalizeText(query).split(/\s+/).filter(Boolean))]
}

/**
 * Rangos del texto original donde aparece algún término. Se normaliza carácter a carácter y se guarda
 * de qué posición original sale cada carácter normalizado, para que el resaltado caiga en su sitio.
 */
export function findRanges(text: string, terms: string[]): TextRange[] {
  if (!text || !terms.length) return []
  let normalized = ''
  const origin: number[] = []
  for (let index = 0; index < text.length; index++) {
    for (const char of normalizeText(text[index])) {
      normalized += char
      origin.push(index)
    }
  }
  const ranges: TextRange[] = []
  for (const term of terms) {
    for (
      let found = normalized.indexOf(term);
      found >= 0;
      found = normalized.indexOf(term, found + term.length)
    ) {
      ranges.push({ start: origin[found], end: origin[found + term.length - 1] + 1 })
    }
  }
  return merge(ranges)
}

function merge(ranges: TextRange[]): TextRange[] {
  const sorted = [...ranges].sort((a, b) => a.start - b.start)
  const merged: TextRange[] = []
  for (const range of sorted) {
    const last = merged[merged.length - 1]
    if (last && range.start <= last.end) last.end = Math.max(last.end, range.end)
    else merged.push({ ...range })
  }
  return merged
}

/** Fragmento de una línea alrededor de la primera coincidencia, para la vista previa de la bandeja. */
export function snippetAround(text: string, terms: string[], radius = 48): string | null {
  const line = text.replace(/\s+/g, ' ').trim()
  const first = findRanges(line, terms)[0]
  if (!first) return null
  const start = Math.max(0, first.start - radius)
  const end = Math.min(line.length, first.end + radius * 2)
  return `${start > 0 ? '…' : ''}${line.slice(start, end).trim()}${end < line.length ? '…' : ''}`
}
