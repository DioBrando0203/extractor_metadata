import { inferSubject, splitThread, stripInlineMarkers } from './thread'

/**
 * Utilidades de presentación para direcciones y textos de correo.
 * Son funciones puras: no conocen la API ni el estado de la cola, sólo transforman texto para mostrarlo.
 */

export interface Address {
  /** Nombre visible; si el correo sólo trae la dirección, se repite aquí. */
  name: string
  email: string | null
}

export interface RecipientGroup {
  label: 'Para' | 'CC' | 'CCO'
  addresses: Address[]
}

const ANGLE_ADDRESS = /^(.*?)\s*<([^<>]+)>\s*$/
const BARE_EMAIL = /^[^\s@<>]+@[^\s@<>]+$/
const RECIPIENT_PREFIX = /^\s*(para|to|cc|cco|bcc)\s*:\s*/i
const GROUP_ORDER: RecipientGroup['label'][] = ['Para', 'CC', 'CCO']
const PREFIX_LABEL: Record<string, RecipientGroup['label']> = {
  para: 'Para',
  to: 'Para',
  cc: 'CC',
  cco: 'CCO',
  bcc: 'CCO',
}

function unquote(value: string): string {
  return value
    .trim()
    .replace(/^(["'])(.*)\1$/, '$2')
    .trim()
}

/** Convierte `Ana Pérez <ana@ejemplo.test>`, `ana@ejemplo.test` o `Ana Pérez` en nombre y correo. */
export function parseAddress(raw: string): Address {
  const value = raw.trim()
  const match = value.match(ANGLE_ADDRESS)
  if (match) {
    const email = match[2].trim()
    return { name: unquote(match[1]) || email, email }
  }
  if (BARE_EMAIL.test(value)) return { name: value, email: value }
  return { name: unquote(value), email: null }
}

/**
 * Separa una lista de destinatarios. El punto y coma siempre separa; la coma sólo cuando el tramo ya
 * contiene una dirección completa, para no partir nombres como `Pérez, Ana <ana@ejemplo.test>`.
 */
export function splitAddresses(raw: string): Address[] {
  const parts: string[] = []
  let current = ''
  let quoted = false
  let angled = false
  for (const char of raw) {
    if (char === '"') quoted = !quoted
    else if (!quoted && char === '<') angled = true
    else if (!quoted && char === '>') angled = false
    const isSeparator =
      !quoted && !angled && (char === ';' || char === '\n' || (char === ',' && /[@>]/.test(current)))
    if (isSeparator) {
      parts.push(current)
      current = ''
    } else {
      current += char
    }
  }
  parts.push(current)
  return parts
    .map((part) => part.trim())
    .filter(Boolean)
    .map(parseAddress)
}

/** Agrupa líneas `Para: …`, `CC: …`, `CCO: …` en el orden en que un lector de correo las muestra. */
export function groupRecipients(lines: string[]): RecipientGroup[] {
  const groups = new Map<RecipientGroup['label'], Address[]>()
  for (const line of lines) {
    const prefix = line.match(RECIPIENT_PREFIX)
    const label = prefix ? PREFIX_LABEL[prefix[1].toLowerCase()] : 'Para'
    const addresses = splitAddresses(prefix ? line.slice(prefix[0].length) : line)
    if (addresses.length) groups.set(label, [...(groups.get(label) ?? []), ...addresses])
  }
  return GROUP_ORDER.filter((label) => groups.has(label)).map((label) => ({
    label,
    addresses: groups.get(label) ?? [],
  }))
}

export function fileStem(fileName: string): string {
  return fileName.replace(/\.msg$/i, '')
}

export type TitleSource = 'subject' | 'inferred' | 'file'

/**
 * Título visible del correo, en orden de confianza: el asunto real; si falta, el asunto del mensaje
 * citado cuando coincide exactamente con el nombre del archivo (Outlook nombra así los `.msg`
 * guardados); y si no, el nombre del archivo. `source` permite avisar al usuario.
 */
export function messageTitle(
  subject: string | null | undefined,
  fileName: string,
  body?: string | null,
): { text: string; source: TitleSource } {
  const clean = subject?.trim()
  if (clean) return { text: clean, source: 'subject' }
  const stem = fileStem(fileName)
  const inferred = body ? inferSubject(stem, splitThread(body).quoted) : null
  return inferred ? { text: inferred, source: 'inferred' } : { text: stem, source: 'file' }
}

/** Primera parte del cuerpo en una sola línea, para la vista previa de la bandeja. */
export function previewLine(body: string | null | undefined, maxLength = 160): string {
  if (!body) return ''
  const line = stripInlineMarkers(body).replace(/\s+/g, ' ').trim()
  return line.length > maxLength ? line.slice(0, maxLength) : line
}
