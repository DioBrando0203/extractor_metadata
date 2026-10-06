import type {
  Attachment,
  AttachmentFile,
  ExtractionResponse,
  ExtractionStatus,
  Message,
  MetadataItem,
  PreviewSource,
} from './types'

const API_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8000/api' : '/api')

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
}

// Sólo imágenes rasterizadas en base64: nunca SVG ni HTML como miniatura.
const PREVIEW_URI = /^data:image\/(jpeg|png|gif|webp);base64,[A-Za-z0-9+/]+=*$/
type ApiMessage = Record<string, unknown> & { headers?: unknown; properties?: unknown; attachments?: unknown }

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
function attachmentList(value: unknown): Attachment[] {
  if (!Array.isArray(value)) return []
  return value.map((item, index) => {
    const attachment = (item ?? {}) as ApiAttachment
    const size = attachment.size_bytes ?? attachment.size
    return {
      name: text(attachment.name ?? attachment.filename, `Adjunto ${index + 1}`),
      content_type: text(attachment.content_type ?? attachment.mime_type) || null,
      size_bytes: typeof size === 'number' ? size : Number(size) || null,
      metadata: items(attachment.metadata, 'Adjunto'),
      warnings: warningList(attachment.warnings),
      ...previewFields(attachment),
      content_id: text(attachment.content_id).trim() || null,
    }
  })
}
function normalizeMessage(payload: ApiMessage, file: File): Message {
  const status: ExtractionStatus = payload.status === 'partial' ? 'partial' : 'complete'
  return {
    file_name: text(payload.file_name, file.name),
    file_size_bytes: typeof payload.file_size_bytes === 'number' ? payload.file_size_bytes : file.size,
    subject: text(payload.subject) || null,
    sender: text(payload.sender) || null,
    recipients: recipientList(payload.recipients),
    sent_at: text(payload.sent_at) || null,
    received_at: text(payload.received_at) || null,
    body_preview: text(payload.body_preview ?? payload.body) || null,
    body_truncated: Boolean(payload.body_truncated),
    headers: items(payload.headers, 'Encabezado'),
    properties: items(payload.properties, 'Propiedad'),
    attachments: attachmentList(payload.attachments),
    warnings: warningList(payload.warnings),
    status,
  }
}

export async function extractMessage(file: File): Promise<ExtractionResponse> {
  const data = new FormData()
  data.append('file', file)
  let response: Response
  try {
    response = await fetch(`${API_URL}/messages/extract`, { method: 'POST', body: data })
  } catch {
    throw new Error('No se pudo conectar con el extractor local. Verifica que el backend esté iniciado.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : body?.detail?.message
    throw new Error(detail || 'No fue posible procesar el archivo.')
  }
  const payload = (await response.json()) as ApiMessage & {
    message?: ApiMessage
    processed_locally?: boolean
  }
  return {
    message: normalizeMessage(payload.message ?? payload, file),
    processed_locally: payload.processed_locally !== false,
  }
}

function filenameFromDisposition(value: string | null, fallback: string): string {
  const encoded = value?.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  if (encoded) return decodeURIComponent(encoded)
  return value?.match(/filename="?([^";]+)"?/i)?.[1] || fallback
}

/**
 * Pide al backend un adjunto. Con `preview` recibe una imagen JPEG generada a partir del adjunto
 * (TIFF, EMF y similares que el navegador no muestra). El MSG se reenvía: el servidor no guarda nada.
 */
export async function fetchAttachment(
  file: File,
  attachmentIndex: number,
  fallbackName: string,
  options: { preview?: boolean } = {},
): Promise<AttachmentFile> {
  const data = new FormData()
  data.append('file', file)
  data.append('attachment_index', String(attachmentIndex))
  if (options.preview) data.append('preview', 'true')
  let response: Response
  try {
    response = await fetch(`${API_URL}/messages/attachment`, { method: 'POST', body: data })
  } catch {
    throw new Error('No se pudo conectar con el extractor local.')
  }
  if (!response.ok) {
    throw new Error(options.preview ? 'Este adjunto no tiene vista previa.' : 'No se pudo abrir el adjunto.')
  }
  return {
    blob: await response.blob(),
    filename: filenameFromDisposition(response.headers.get('content-disposition'), fallbackName),
  }
}

/** Inicia la descarga de un binario ya presente en memoria y libera la URL temporal. */
export function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export async function downloadAttachment(file: File, attachmentIndex: number, fallbackName: string) {
  const attachment = await fetchAttachment(file, attachmentIndex, fallbackName)
  saveBlob(attachment.blob, attachment.filename)
}
