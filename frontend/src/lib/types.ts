export type ExtractionStatus = 'complete' | 'partial'
export type QueueStatus = 'queued' | 'extracting' | 'complete' | 'partial' | 'error'

export interface MetadataItem {
  group: string
  label: string
  value: string
}
export type PreviewSource = 'image' | 'embedded'

export interface Attachment {
  name: string
  content_type?: string | null
  size_bytes?: number | null
  metadata: MetadataItem[]
  warnings: string[]
  /** Miniatura como data URI de imagen; `embedded` si la guardó el propio archivo (DWG, DXF, Office). */
  preview?: string | null
  preview_source?: PreviewSource | null
}

export interface AttachmentFile {
  blob: Blob
  filename: string
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
