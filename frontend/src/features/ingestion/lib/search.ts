import type { QueueItem } from '../../../lib/types'

/** Minúsculas y sin tildes: "Revisión" coincide con "revision". */
export function normalize(text: string): string {
  return text.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
}

function searchableText(item: QueueItem): string {
  const message = item.message
  const parts = [item.file.name]
  if (message) {
    parts.push(
      message.subject ?? '',
      message.sender ?? '',
      ...message.recipients,
      message.body_preview ?? '',
      ...message.attachments.map((attachment) => attachment.name),
    )
  }
  return normalize(parts.join('\n'))
}

/** Filtra la bandeja: todas las palabras de la búsqueda deben aparecer en el correo. */
export function filterQueue(items: QueueItem[], query: string): QueueItem[] {
  const words = normalize(query).split(/\s+/).filter(Boolean)
  if (!words.length) return items
  return items.filter((item) => {
    const text = searchableText(item)
    return words.every((word) => text.includes(word))
  })
}
