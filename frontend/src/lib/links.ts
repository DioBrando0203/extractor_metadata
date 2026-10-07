/*
 * Direcciones web dentro de datos del correo (cuerpo y adjuntos por referencia). Sólo http y https se
 * ofrecen como enlace (ADR-19): `file:`, `javascript:` o una ruta de red quedan como texto.
 */

const WEB_LINK = /^https?:\/\/[^\s/]+\S*$/i
const URL_IN_TEXT = /https?:\/\/[^\s<>"]+/gi
/** Puntuación que cierra una frase o un `<…>` y no forma parte de la dirección. */
const TRAILING = /[.,;:!?)\]}'"]+$/

export function isWebLink(link: string | null | undefined): link is string {
  return Boolean(link && WEB_LINK.test(link))
}

export type TextSegment = { text: string; link?: string }

/** Parte un texto en tramos de texto y de dirección web, sin alterar ningún carácter. */
export function splitLinks(text: string): TextSegment[] {
  const segments: TextSegment[] = []
  let last = 0
  for (const match of text.matchAll(URL_IN_TEXT)) {
    const url = match[0].replace(TRAILING, '')
    const start = match.index ?? 0
    if (!isWebLink(url) || start < last) continue
    if (start > last) segments.push({ text: text.slice(last, start) })
    segments.push({ text: url, link: url })
    last = start + url.length
  }
  if (last < text.length) segments.push({ text: text.slice(last) })
  return segments
}
