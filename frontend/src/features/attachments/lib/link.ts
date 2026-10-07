import { isWebLink } from '../../../lib/links'

/**
 * Adjuntos por referencia (`kind: 'link'`): el archivo vive en la nube o en una carpeta compartida y el
 * correo sólo guarda su dirección. La regla de qué se abre como enlace está en `lib/links.ts`.
 */
export { isWebLink }

/** Dónde vive el archivo, en palabras del usuario. */
export function linkPlace(link: string | null | undefined): string {
  if (!link) return 'Enlace sin dirección'
  return isWebLink(link) ? 'Enlace web' : 'Carpeta compartida'
}
