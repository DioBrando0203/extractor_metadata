import { normalizeMessage } from './normalize'
import type { ApiMessage } from './normalize'
import type { AttachmentFile, ExtractionResponse } from './types'

const API_URL = import.meta.env.VITE_API_URL ?? (import.meta.env.DEV ? 'http://127.0.0.1:8000/api' : '/api')

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
    message: normalizeMessage(payload.message ?? payload, { name: file.name, size: file.size }),
    processed_locally: payload.processed_locally !== false,
  }
}

function filenameFromDisposition(value: string | null, fallback: string): string {
  const encoded = value?.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  if (encoded) return decodeURIComponent(encoded)
  return value?.match(/filename="?([^";]+)"?/i)?.[1] || fallback
}

export type AttachmentOptions = {
  /** Imagen JPEG generada a partir del adjunto (TIFF, EMF y similares que el navegador no muestra). */
  preview?: boolean
  /** Posiciones de los correos adjuntos que hay que abrir para llegar al adjunto. */
  messagePath?: readonly number[]
}

/** Pide al backend un adjunto. El MSG se reenvía: el servidor no guarda nada. */
export async function fetchAttachment(
  file: File,
  attachmentIndex: number,
  fallbackName: string,
  options: AttachmentOptions = {},
): Promise<AttachmentFile> {
  const data = new FormData()
  data.append('file', file)
  data.append('attachment_index', String(attachmentIndex))
  if (options.preview) data.append('preview', 'true')
  if (options.messagePath?.length) data.append('message_path', options.messagePath.join('/'))
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

/** Todos los adjuntos descargables del correo (o correo adjunto) en un ZIP armado por el backend. */
export async function fetchAllAttachments(
  file: File,
  messagePath: readonly number[] = [],
): Promise<AttachmentFile> {
  const data = new FormData()
  data.append('file', file)
  if (messagePath.length) data.append('message_path', messagePath.join('/'))
  let response: Response
  try {
    response = await fetch(`${API_URL}/messages/attachments`, { method: 'POST', body: data })
  } catch {
    throw new Error('No se pudo conectar con el extractor local.')
  }
  if (!response.ok) throw new Error('No se pudieron preparar los adjuntos.')
  return {
    blob: await response.blob(),
    // Entre orígenes (desarrollo, LAN) el navegador no deja leer Content-Disposition: mismo nombre que el backend.
    filename: filenameFromDisposition(
      response.headers.get('content-disposition'),
      `${file.name.replace(/\.msg$/i, '')} - adjuntos.zip`,
    ),
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

/** Convierte un KML/KMZ local; el backend devuelve un ZIP temporal con el GeoPackage. */
export async function convertGeodata(file: File): Promise<AttachmentFile> {
  const data = new FormData()
  data.append('file', file)
  let response: Response
  try {
    response = await fetch(`${API_URL}/geodata/convert`, { method: 'POST', body: data })
  } catch {
    throw new Error('No se pudo conectar con el conversor local.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : body?.detail?.message
    throw new Error(detail || 'No fue posible convertir el archivo.')
  }
  return {
    blob: await response.blob(),
    filename: filenameFromDisposition(
      response.headers.get('content-disposition'),
      `${file.name.replace(/\.km[zl]$/i, '')} - convertido.zip`,
    ),
  }
}
