export type ExtractionStatus = 'complete' | 'partial'
export type QueueStatus = 'queued' | 'extracting' | 'complete' | 'partial' | 'error'

export interface MetadataItem {
  group: string
  label: string
  value: string
}
export type PreviewSource = 'image' | 'embedded'
/** Cómo viaja un adjunto: con sus bytes, como correo adjunto o como enlace a la nube o a una ruta. */
export type AttachmentKind = 'file' | 'message' | 'link'

export interface Attachment {
  name: string
  content_type?: string | null
  size_bytes?: number | null
  metadata: MetadataItem[]
  warnings: string[]
  /** Miniatura como data URI de imagen; `embedded` si la guardó el propio archivo (DWG, DXF, Office). */
  preview?: string | null
  preview_source?: PreviewSource | null
  /** Content-ID con el que el cuerpo marca la posición de la imagen como `[cid:…]`. */
  content_id?: string | null
  /** El Content-ID se reconstruyó por las medidas de la imagen (archivo dañado). */
  content_id_inferred?: boolean
  /** Sin valor equivale a `file`. */
  kind?: AttachmentKind
  /** Dirección de un adjunto `link` (URL o ruta de red), como texto. */
  link?: string | null
  /** Correo adjunto ya leído por el backend; `null` si no se pudo abrir. */
  message?: Message | null
}

export interface AttachmentFile {
  blob: Blob
  filename: string
}
/** Correo S/MIME (firmado en claro, opaco o cifrado) o con permisos IRM. */
export type Security = 'signed' | 'opaque' | 'encrypted' | 'protected'
/** Qué es un MSG que no es un correo. */
export type ItemKind = 'meeting' | 'cancellation' | 'response' | 'appointment' | 'contact' | 'task'

export interface ItemDetails {
  kind: ItemKind
  /** Reunión o cita: inicio y fin. Tarea: inicio y vencimiento. ISO-8601. */
  start?: string | null
  end?: string | null
  all_day: boolean
  location?: string | null
  /** Organizador, asistentes, repetición, respuesta, teléfonos, estado… en orden. */
  fields: MetadataItem[]
}
export interface Message {
  file_name: string
  file_size_bytes: number
  subject?: string | null
  sender?: string | null
  recipients: string[]
  sent_at?: string | null
  received_at?: string | null
  body_preview?: string | null
  body_truncated: boolean
  headers: MetadataItem[]
  properties: MetadataItem[]
  attachments: Attachment[]
  warnings: string[]
  status: ExtractionStatus
  /** Reunión, cita, contacto o tarea; `null` en un correo. */
  item?: ItemDetails | null
  security?: Security | null
}
export interface ExtractionResponse {
  message: Message
  processed_locally: boolean
}
export interface QueueItem {
  id: string
  file: File
  status: QueueStatus
  message?: Message
  error?: string
}
