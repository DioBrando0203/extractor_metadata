const LOCALE = 'es-PE'

const sizeFormat = new Intl.NumberFormat(LOCALE, { maximumFractionDigits: 1 })
const mediumDate = new Intl.DateTimeFormat(LOCALE, { dateStyle: 'medium', timeStyle: 'short' })
const mailDate = new Intl.DateTimeFormat(LOCALE, {
  weekday: 'short',
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})
const timeOnly = new Intl.DateTimeFormat(LOCALE, { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })
const dayMonth = new Intl.DateTimeFormat(LOCALE, { day: 'numeric', month: 'short' })
const shortDate = new Intl.DateTimeFormat(LOCALE, { day: '2-digit', month: '2-digit', year: '2-digit' })

export function formatBytes(bytes?: number | null): string {
  if (bytes == null || !Number.isFinite(bytes) || bytes < 0) return '—'
  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = bytes > 0 ? Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), 3) : 0
  return `${sizeFormat.format(bytes / 1024 ** exponent)} ${units[exponent]}`
}

export function parseDate(value?: string | null): Date | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDate(value?: string | null): string {
  const date = parseDate(value)
  return date ? mediumDate.format(date) : 'Sin fecha'
}

/** Fecha completa del encabezado del correo, p. ej. `lun 05/10/2026, 20:13`. */
export function formatMailDate(value?: string | null): string | null {
  const date = parseDate(value)
  return date ? mailDate.format(date) : null
}

/** Fecha compacta de la bandeja: hora si es de hoy, día y mes si es de este año y fecha corta si no. */
export function formatListDate(value?: string | null, now: Date = new Date()): string | null {
  const date = parseDate(value)
  if (!date) return null
  if (date.toDateString() === now.toDateString()) return timeOnly.format(date)
  if (date.getFullYear() === now.getFullYear()) return dayMonth.format(date)
  return shortDate.format(date)
}

/**
 * Limpia el texto del cuerpo sólo en su presentación: unifica saltos de línea, quita espacios al final
 * de cada línea y reduce bloques de líneas vacías (frecuentes al convertir HTML a texto).
 */
export function tidyText(value?: string | null): string {
  if (!value) return ''
  return value
    .replace(/\r\n?/g, '\n')
    .replace(/[ \t\u00a0]+$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
