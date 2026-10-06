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

/**
 * Título visible del correo. Outlook nombra los `.msg` guardados con el asunto, así que el nombre del
 * archivo es el mejor sustituto cuando el asunto no se recuperó; `fromFileName` permite avisarlo.
 */
export function messageTitle(
  subject: string | null | undefined,
  fileName: string,
): { text: string; fromFileName: boolean } {
  const clean = subject?.trim()
  return clean ? { text: clean, fromFileName: false } : { text: fileStem(fileName), fromFileName: true }
}

/** Primera parte del cuerpo en una sola línea, para la vista previa de la bandeja. */
export function previewLine(body: string | null | undefined, maxLength = 160): string {
  if (!body) return ''
  const line = body.replace(/\s+/g, ' ').trim()
  return line.length > maxLength ? line.slice(0, maxLength) : line
}
