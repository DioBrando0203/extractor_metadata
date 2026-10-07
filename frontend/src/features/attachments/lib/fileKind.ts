import { formatBytes } from '../../../lib/formatters'
import type { Attachment } from '../../../lib/types'
import { linkPlace } from './link'

export type FileKind =
  'pdf' | 'word' | 'excel' | 'slides' | 'image' | 'cad' | 'archive' | 'mail' | 'text' | 'media' | 'other'

const BY_EXTENSION: Record<string, FileKind> = {
  pdf: 'pdf',
  doc: 'word',
  docx: 'word',
  docm: 'word',
  dot: 'word',
  dotx: 'word',
  rtf: 'word',
  odt: 'word',
  xls: 'excel',
  xlsx: 'excel',
  xlsm: 'excel',
  xlsb: 'excel',
  csv: 'excel',
  ods: 'excel',
  ppt: 'slides',
  pptx: 'slides',
  pptm: 'slides',
  odp: 'slides',
  png: 'image',
  jpg: 'image',
  jpeg: 'image',
  gif: 'image',
  bmp: 'image',
  tif: 'image',
  tiff: 'image',
  webp: 'image',
  svg: 'image',
  heic: 'image',
  emf: 'image',
  wmf: 'image',
  dwg: 'cad',
  dxf: 'cad',
  dwf: 'cad',
  dgn: 'cad',
  zip: 'archive',
  rar: 'archive',
  '7z': 'archive',
  gz: 'archive',
  tar: 'archive',
  msg: 'mail',
  eml: 'mail',
  txt: 'text',
  log: 'text',
  xml: 'text',
  json: 'text',
  htm: 'text',
  html: 'text',
  mp3: 'media',
  wav: 'media',
  mp4: 'media',
  mov: 'media',
  avi: 'media',
}

const KIND_LABEL: Record<FileKind, string> = {
  pdf: 'PDF',
  word: 'Documento',
  excel: 'Hoja de cálculo',
  slides: 'Presentación',
  image: 'Imagen',
  cad: 'Plano CAD',
  archive: 'Comprimido',
  mail: 'Correo',
  text: 'Texto',
  media: 'Multimedia',
  other: 'Archivo',
}

export function extensionOf(name: string): string {
  return name.match(/\.([a-z0-9]{1,8})$/i)?.[1].toLowerCase() ?? ''
}

/** Clasifica un adjunto por extensión y, si no la tiene, por su tipo MIME. Sólo se usa para el icono. */
export function fileKind(name: string, contentType?: string | null): FileKind {
  const byExtension = BY_EXTENSION[extensionOf(name)]
  if (byExtension) return byExtension
  const type = contentType?.toLowerCase() ?? ''
  if (type === 'application/pdf') return 'pdf'
  if (type.startsWith('image/')) return 'image'
  if (type.includes('wordprocessingml') || type === 'application/msword') return 'word'
  if (type.includes('spreadsheetml') || type.includes('ms-excel')) return 'excel'
  if (type.includes('presentationml') || type.includes('ms-powerpoint')) return 'slides'
  if (type.includes('dwg') || type.includes('dxf')) return 'cad'
  if (type.includes('zip') || type.includes('compressed')) return 'archive'
  if (type === 'message/rfc822' || type.includes('ms-outlook')) return 'mail'
  if (type.startsWith('text/')) return 'text'
  if (type.startsWith('audio/') || type.startsWith('video/')) return 'media'
  return 'other'
}

/** Etiqueta breve del tipo: la extensión en mayúsculas o, si falta, una descripción genérica. */
export function kindLabel(name: string, contentType?: string | null): string {
  const extension = extensionOf(name)
  return extension ? extension.toUpperCase() : KIND_LABEL[fileKind(name, contentType)]
}

/**
 * Icono y etiqueta de un adjunto. Un correo adjunto se llama como su asunto ("Informe v1.2"), así que
 * no se deduce su tipo por una falsa extensión.
 */
export function describeAttachment(attachment: Pick<Attachment, 'name' | 'content_type' | 'kind'>): {
  kind: FileKind
  label: string
} {
  if (attachment.kind === 'message') return { kind: 'mail', label: KIND_LABEL.mail }
  const { name, content_type: contentType } = attachment
  return { kind: fileKind(name, contentType), label: kindLabel(name, contentType) }
}

/** "TIPO · tamaño"; un enlace no tiene tamaño, sino un lugar (web o carpeta compartida). */
export function attachmentMeta(
  attachment: Pick<Attachment, 'name' | 'content_type' | 'kind' | 'size_bytes' | 'link'>,
): string {
  const { label } = describeAttachment(attachment)
  if (attachment.kind === 'link') return `${label} · ${linkPlace(attachment.link)}`
  return `${label} · ${formatBytes(attachment.size_bytes)}`
}
