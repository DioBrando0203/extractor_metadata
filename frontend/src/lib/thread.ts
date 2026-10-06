/**
 * Estructura del cuerpo de un correo en texto plano: el mensaje actual, los mensajes citados del hilo
 * (bloques De/Enviado/Para/Asunto que Outlook inserta al responder) y las imágenes incrustadas
 * marcadas como `[cid:…]`. Funciones puras: no conocen React ni la API.
 */

import type { Attachment } from './types'

export type BodyPart = { kind: 'text'; text: string } | { kind: 'image'; cid: string }

export interface QuotedField {
  label: 'De' | 'Enviado' | 'Para' | 'CC' | 'CCO' | 'Asunto'
  value: string
}

export interface QuotedMessage {
  fields: QuotedField[]
  body: string
}

export interface Thread {
  current: string
  quoted: QuotedMessage[]
}

const FIELD =
  /^\s*\*?\s*(de|from|enviado(?: el)?|sent|fecha|date|para|to|cc|cco|bcc|asunto|subject)\s*\*?\s*:\s*(.*)$/i
const LABELS: Record<string, QuotedField['label']> = {
  de: 'De',
  from: 'De',
  enviado: 'Enviado',
  'enviado el': 'Enviado',
  sent: 'Enviado',
  fecha: 'Enviado',
  date: 'Enviado',
  para: 'Para',
  to: 'Para',
  cc: 'CC',
  cco: 'CCO',
  bcc: 'CCO',
  asunto: 'Asunto',
  subject: 'Asunto',
}
/** Líneas que Outlook pone antes de un mensaje citado. */
const SEPARATOR = /^\s*(_{8,}|-{3,}\s*(original message|mensaje original)\s*-{3,}|-{8,})\s*$/i
/** Un bloque citado empieza con De/From y debe llegar a Asunto/Subject en pocas líneas. */
const MAX_HEADER_LINES = 10
const CID = /\[cid:([^\]\s]+)\]/gi

function fieldOf(line: string): QuotedField | null {
  const match = line.match(FIELD)
  if (!match) return null
  const label = LABELS[match[1].toLowerCase().replace(/\s+/g, ' ')]
  return label ? { label, value: match[2].trim() } : null
}

/** Busca un bloque de encabezado citado que empiece en `start`; devuelve sus campos y la línea final. */
function headerAt(lines: string[], start: number): { fields: QuotedField[]; end: number } | null {
  const first = fieldOf(lines[start])
  if (first?.label !== 'De') return null
  const fields: QuotedField[] = [first]
  for (let index = start + 1; index < Math.min(lines.length, start + MAX_HEADER_LINES); index++) {
    const field = fieldOf(lines[index])
    if (field) fields.push(field)
    else if (lines[index].trim() && fields.length)
      fields[fields.length - 1].value += ` ${lines[index].trim()}`
    if (field?.label === 'Asunto') return { fields, end: index }
  }
  return null
}

function trimSeparators(text: string): string {
  const lines = text.split('\n')
  while (lines.length && (!lines[lines.length - 1].trim() || SEPARATOR.test(lines[lines.length - 1])))
    lines.pop()
  while (lines.length && !lines[0].trim()) lines.shift()
  return lines.join('\n')
}

/** Separa el mensaje actual de los mensajes citados, del más reciente al más antiguo. */
export function splitThread(text: string): Thread {
  const lines = text.split('\n')
  const blocks: { fields: QuotedField[]; start: number; end: number }[] = []
  for (let index = 0; index < lines.length; index++) {
    const header = headerAt(lines, index)
    if (header) {
      blocks.push({ ...header, start: index })
      index = header.end
    }
  }
  if (!blocks.length) return { current: text, quoted: [] }
  const quoted = blocks.map((block, position) => {
    const until = position + 1 < blocks.length ? blocks[position + 1].start : lines.length
    return { fields: block.fields, body: trimSeparators(lines.slice(block.end + 1, until).join('\n')) }
  })
  return { current: trimSeparators(lines.slice(0, blocks[0].start).join('\n')), quoted }
}

/** Divide un texto en tramos de texto e imágenes incrustadas, en el orden en que aparecen. */
export function parseInline(text: string): BodyPart[] {
  const parts: BodyPart[] = []
  let last = 0
  for (const match of text.matchAll(CID)) {
    const before = text.slice(last, match.index).replace(/\n+$/, '')
    if (before.trim()) parts.push({ kind: 'text', text: before.replace(/^\n+/, '') })
    parts.push({ kind: 'image', cid: match[1] })
    last = (match.index ?? 0) + match[0].length
  }
  const rest = text.slice(last).replace(/^\n+/, '')
  if (rest.trim()) parts.push({ kind: 'text', text: rest })
  return parts
}

/** Índice del adjunto al que apunta un `cid`: por Content-ID exacto o por el nombre antes de `@`. */
export function findInlineAttachment(cid: string, attachments: Attachment[]): number {
  const wanted = cid.toLowerCase()
  const byId = attachments.findIndex((item) => item.content_id?.toLowerCase() === wanted)
  if (byId >= 0) return byId
  const name = wanted.split('@')[0]
  return attachments.findIndex((item) => item.name.toLowerCase() === name)
}

/** Adjuntos que el cuerpo muestra en su posición (se excluyen de la lista superior). */
export function inlineAttachmentIndices(text: string, attachments: Attachment[]): Set<number> {
  const indices = new Set<number>()
  for (const match of text.matchAll(CID)) {
    const index = findInlineAttachment(match[1], attachments)
    if (index >= 0) indices.add(index)
  }
  return indices
}

/** Caracteres que Windows no admite en nombres; Outlook los cambia por `_` al guardar un `.msg`. */
const INVALID_FILENAME = /[<>:"/\\|?*]/g
const REPLY_PREFIXES = ['', 'RE: ', 'RV: ', 'FW: ', 'Fwd: ', 'Re: ', 'Fw: ', 'RE:', 'RV:']

/**
 * Deduce el asunto cuando el MSG lo perdió: toma el asunto del primer mensaje citado y sólo lo acepta
 * si, guardado con las reglas de Outlook, produce exactamente el nombre del archivo.
 */
export function inferSubject(fileStem: string, quoted: QuotedMessage[]): string | null {
  const original = quoted.find((message) => message.fields.some((field) => field.label === 'Asunto'))
  const subject = original?.fields.find((field) => field.label === 'Asunto')?.value.trim()
  if (!subject) return null
  const bare = subject.replace(/^((re|rv|fw|fwd)\s*:\s*)+/i, '')
  const candidates = [subject, ...REPLY_PREFIXES.map((prefix) => `${prefix}${bare}`)]
  return (
    candidates.find((candidate) => candidate.replace(INVALID_FILENAME, '_').trim() === fileStem.trim()) ??
    null
  )
}
