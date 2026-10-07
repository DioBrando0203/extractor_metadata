import { normalizeText, searchTerms, snippetAround } from '../../../lib/textSearch'
import { stripInlineMarkers } from '../../../lib/thread'
import type { Message, QueueItem } from '../../../lib/types'

/** Asunto, personas, texto (con historial) y adjuntos de un correo y de los correos adjuntos que contiene. */
function messageParts(message: Message): string[] {
  return [
    message.subject ?? '',
    message.sender ?? '',
    ...message.recipients,
    stripInlineMarkers(message.body_preview ?? ''),
    ...message.attachments.flatMap((attachment) => [
      attachment.name,
      ...(attachment.message ? messageParts(attachment.message) : []),
    ]),
  ]
}

/** Todo lo buscable de un elemento de la bandeja: el nombre del archivo y su correo. */
function searchableText(item: QueueItem): string {
  const parts = [item.file.name, ...(item.message ? messageParts(item.message) : [])]
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

/** La coincidencia está dentro de un correo adjunto: se dice en cuál y, si se puede, dónde. */
function attachedMessageMatch(message: Message, terms: string[]): string | null {
  for (const attachment of message.attachments) {
    const inner = attachment.message
    if (!inner) continue
    const text = normalizeText(messageParts(inner).join('\n'))
    if (!terms.some((term) => text.includes(term))) continue
    const snippet = snippetAround(stripInlineMarkers(inner.body_preview ?? ''), terms)
    return snippet ? `Correo adjunto «${attachment.name}»: ${snippet}` : `Correo adjunto: ${attachment.name}`
  }
  return null
}

/**
 * Fragmento que explica por qué un correo coincide: el texto alrededor de la palabra buscada o, si
 * está en un adjunto, en los destinatarios o en un correo adjunto, esa referencia. `null` si coincide
 * sólo por remitente o asunto, que ya se ven en la fila.
 */
export function matchPreview(message: Message, terms: string[]): string | null {
  if (!terms.length) return null
  const body = snippetAround(stripInlineMarkers(message.body_preview ?? ''), terms)
  if (body) return body
  const attachment = message.attachments.find((item) => snippetAround(item.name, terms))
  if (attachment) return `Adjunto: ${attachment.name}`
  return snippetAround(message.recipients.join(' · '), terms) ?? attachedMessageMatch(message, terms)
}
