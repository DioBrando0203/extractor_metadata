import type {
  Attachment,
  AttachmentKind,
  ExtractionStatus,
  Message,
  MetadataItem,
  PreviewSource,
} from './types'

/*
 * Normalización del JSON del backend al contrato de `types.ts`. Tolera campos ausentes o con otro
 * nombre y valida lo sensible (miniaturas), así la UI nunca recibe `unknown` (P-02).
 */

type ApiItem = { group?: unknown; label?: unknown; name?: unknown; key?: unknown; value?: unknown }
type ApiAttachment = {
  name?: unknown
  filename?: unknown
  content_type?: unknown
  mime_type?: unknown
  size_bytes?: unknown
  size?: unknown
  metadata?: unknown
  warnings?: unknown
  preview?: unknown
  preview_source?: unknown
  content_id?: unknown
  content_id_inferred?: unknown
  kind?: unknown
  link?: unknown
  message?: unknown
}
export type ApiMessage = Record<string, unknown> & {
  headers?: unknown
  properties?: unknown
  attachments?: unknown
}
/** Datos del archivo que sustituyen a los que falten en la respuesta. */
type Fallback = { name: string; size: number }

// Sólo imágenes rasterizadas en base64: nunca SVG ni HTML como miniatura.
const PREVIEW_URI = /^data:image\/(jpeg|png|gif|webp);base64,[A-Za-z0-9+/]+=*$/
/** El backend abre hasta 3 niveles; más allá se ignora para no recorrer datos inesperados sin fin. */
const MAX_NESTED_MESSAGES = 5

function text(value: unknown, fallback = ''): string {
  return typeof value === 'string' ? value : value == null ? fallback : String(value)
}
function items(value: unknown, group: string): MetadataItem[] {
  if (!Array.isArray(value)) return []
  return value.map((item, index) => {
    const row = (item ?? {}) as ApiItem
    return {
      group: text(row.group, group),
      label: text(row.label ?? row.name ?? row.key, `Campo ${index + 1}`),
      value: text(row.value, '—'),
    }
  })
}
function warningList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => text(item)).filter(Boolean) : []
}
function recipientList(value: unknown): string[] {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => text(item))
    .filter(Boolean)
    .map((item) => (/^(para|to|cc|cco|bcc)\s*:/i.test(item) ? item : `Para: ${item}`))
}
function previewFields(attachment: ApiAttachment): Pick<Attachment, 'preview' | 'preview_source'> {
  const preview = typeof attachment.preview === 'string' ? attachment.preview : ''
  if (!PREVIEW_URI.test(preview)) return { preview: null, preview_source: null }
  const source: PreviewSource = attachment.preview_source === 'embedded' ? 'embedded' : 'image'
  return { preview, preview_source: source }
}
function kindFields(attachment: ApiAttachment, fallback: Fallback, depth: number) {
  const kind: AttachmentKind =
    attachment.kind === 'message' || attachment.kind === 'link' ? attachment.kind : 'file'
  const inner = attachment.message
  const message =
    kind === 'message' && inner && typeof inner === 'object' && depth < MAX_NESTED_MESSAGES
      ? normalizeMessage(inner as ApiMessage, fallback, depth + 1)
      : null
  const link = kind === 'link' ? text(attachment.link).trim() || null : null
  return { kind, link, message }
}
function attachmentList(value: unknown, depth: number): Attachment[] {
  if (!Array.isArray(value)) return []
  return value.map((item, index) => {
    const attachment = (item ?? {}) as ApiAttachment
    const size = attachment.size_bytes ?? attachment.size
    const name = text(attachment.name ?? attachment.filename, `Adjunto ${index + 1}`)
    const size_bytes = typeof size === 'number' ? size : Number(size) || null
    return {
      name,
      content_type: text(attachment.content_type ?? attachment.mime_type) || null,
      size_bytes,
      metadata: items(attachment.metadata, 'Adjunto'),
      warnings: warningList(attachment.warnings),
      ...previewFields(attachment),
      content_id: text(attachment.content_id).trim() || null,
      content_id_inferred: attachment.content_id_inferred === true,
      ...kindFields(attachment, { name: `${name}.msg`, size: size_bytes ?? 0 }, depth),
    }
  })
}

export function normalizeMessage(payload: ApiMessage, fallback: Fallback, depth = 0): Message {
  const status: ExtractionStatus = payload.status === 'partial' ? 'partial' : 'complete'
  return {
    file_name: text(payload.file_name, fallback.name),
    file_size_bytes: typeof payload.file_size_bytes === 'number' ? payload.file_size_bytes : fallback.size,
    subject: text(payload.subject) || null,
    sender: text(payload.sender) || null,
    recipients: recipientList(payload.recipients),
    sent_at: text(payload.sent_at) || null,
    received_at: text(payload.received_at) || null,
    body_preview: text(payload.body_preview ?? payload.body) || null,
    body_truncated: Boolean(payload.body_truncated),
    headers: items(payload.headers, 'Encabezado'),
    properties: items(payload.properties, 'Propiedad'),
    attachments: attachmentList(payload.attachments, depth),
    warnings: warningList(payload.warnings),
    status,
  }
}
