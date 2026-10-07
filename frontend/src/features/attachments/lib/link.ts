const WEB_LINK = /^https?:\/\/[^\s/]+\S*$/i

/**
 * Adjuntos por referencia (`kind: 'link'`): el archivo vive en la nube o en una carpeta compartida y el
 * correo sólo guarda su dirección. Sólo http y https se ofrecen como enlace; una ruta de red o cualquier
 * otro esquema (`file:`, `javascript:`) se muestra como texto.
 */
export function isWebLink(link: string | null | undefined): link is string {
  return Boolean(link && WEB_LINK.test(link))
}

/** Dónde vive el archivo, en palabras del usuario. */
export function linkPlace(link: string | null | undefined): string {
  if (!link) return 'Enlace sin dirección'
  return isWebLink(link) ? 'Enlace web' : 'Carpeta compartida'
}
