import { normalizeText, searchTerms, snippetAround } from '../../../lib/textSearch'
import { stripInlineMarkers } from '../../../lib/thread'
import type { Message, QueueItem } from '../../../lib/types'

/** Todo lo buscable de un correo: archivo, asunto, personas, texto (con historial) y adjuntos. */
function searchableText(item: QueueItem): string {
  const message = item.message
  const parts = [item.file.name]
  if (message) {
    parts.push(
      message.subject ?? '',
      message.sender ?? '',
      ...message.recipients,
      stripInlineMarkers(message.body_preview ?? ''),
      ...message.attachments.map((attachment) => attachment.name),
    )
  }
  return normalizeText(parts.join('\n'))
}

/** Filtra la bandeja: todas las palabras de la búsqueda deben aparecer en el correo. */
export function filterQueue(items: QueueItem[], query: string): QueueItem[] {
  const terms = searchTerms(query)
  if (!terms.length) return items
  return items.filter((item) => {
    const text = searchableText(item)
    return terms.every((term) => text.includes(term))
  })
}

/**
 * Fragmento que explica por qué un correo coincide: el texto alrededor de la palabra buscada o, si
 * está en un adjunto o en los destinatarios, esa referencia. `null` si coincide sólo por remitente o
 * asunto, que ya se ven en la fila.
 */
export function matchPreview(message: Message, terms: string[]): string | null {
  if (!terms.length) return null
  const body = snippetAround(stripInlineMarkers(message.body_preview ?? ''), terms)
  if (body) return body
  const attachment = message.attachments.find((item) => snippetAround(item.name, terms))
  if (attachment) return `Adjunto: ${attachment.name}`
  return snippetAround(message.recipients.join(' · '), terms)
}
