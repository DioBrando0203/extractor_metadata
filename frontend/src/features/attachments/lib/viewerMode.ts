import type { Attachment } from '../../../lib/types'
import { extensionOf, fileKind } from './fileKind'

/**
 * Cómo se puede ver un adjunto sin descargarlo:
 * - image: el navegador lo muestra tal cual.
 * - converted: imagen que el navegador no soporta (TIFF, EMF…); el backend la convierte a JPEG.
 * - pdf: visor de PDF del navegador.
 * - text, video, audio: elementos nativos, siempre como datos y nunca como HTML.
 * - embedded: sólo la miniatura que el propio archivo guardó (DWG, DXF, Office).
 * - message: correo adjunto; se ofrece abrirlo como un correo propio.
 * - link: archivo en la nube o en una carpeta compartida; sólo hay una dirección.
 * - none: sin vista previa; se ofrece descargar.
 */
export type ViewerMode =
  'image' | 'converted' | 'pdf' | 'text' | 'video' | 'audio' | 'embedded' | 'message' | 'link' | 'none'

const NATIVE_IMAGES = new Set(['png', 'jpg', 'jpeg', 'jfif', 'gif', 'webp', 'bmp', 'ico', 'avif', 'svg'])
const NATIVE_IMAGE_TYPES = new Set(['image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/bmp'])
const CONVERTIBLE_IMAGES = new Set(['tif', 'tiff', 'emf', 'wmf', 'dib'])
const TEXT = new Set([
  'txt',
  'csv',
  'tsv',
  'log',
  'json',
  'xml',
  'md',
  'ini',
  'cfg',
  'conf',
  'yaml',
  'yml',
  'sql',
  'eml',
  'ics',
  'vcs',
  'vcf',
  'htm',
  'html',
])
const NO_FILE = new Set<ViewerMode>(['embedded', 'message', 'link', 'none'])
const VIDEO = new Set(['mp4', 'm4v', 'webm', 'ogv', 'mov'])
const AUDIO = new Set(['mp3', 'wav', 'ogg', 'oga', 'm4a', 'aac', 'flac'])

export function viewerMode(
  attachment: Pick<Attachment, 'name' | 'content_type' | 'preview_source' | 'kind'>,
): ViewerMode {
  if (attachment.kind === 'message' || attachment.kind === 'link') return attachment.kind
  const extension = extensionOf(attachment.name)
  const type = attachment.content_type?.toLowerCase() ?? ''
  if (NATIVE_IMAGES.has(extension) || (!extension && NATIVE_IMAGE_TYPES.has(type))) return 'image'
  if (CONVERTIBLE_IMAGES.has(extension)) return 'converted'
  if (attachment.preview_source === 'image' && fileKind(attachment.name, type) === 'image') return 'converted'
  if (fileKind(attachment.name, type) === 'pdf') return 'pdf'
  if (TEXT.has(extension) || (!extension && type.startsWith('text/'))) return 'text'
  if (VIDEO.has(extension)) return 'video'
  if (AUDIO.has(extension)) return 'audio'
  if (attachment.preview_source === 'embedded') return 'embedded'
  return 'none'
}

/** El modo necesita pedir el archivo al backend (los demás usan la miniatura o nada). */
export function needsFile(mode: ViewerMode): boolean {
  return !NO_FILE.has(mode)
}

/**
 * Tipo MIME que el navegador necesita para mostrar el binario. `undefined` conserva el del backend
 * (el JPEG de `converted`, vídeo y audio ya llegan con su tipo).
 */
export function blobTypeFor(mode: ViewerMode, name: string): string | undefined {
  if (mode === 'pdf') return 'application/pdf'
  if (mode === 'image' && extensionOf(name) === 'svg') return 'image/svg+xml'
  return undefined
}

/** Texto máximo que se muestra en el visor; el resto queda para la descarga. */
export const TEXT_PREVIEW_LIMIT = 1024 * 1024
