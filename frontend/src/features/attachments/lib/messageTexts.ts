import { formatMailDate, parseDate, tidyText } from '../../../lib/formatters'
import { groupRecipients, parseAddress } from '../../../lib/mail'
import { splitThread } from '../../../lib/thread'
import { parseQuotedDate } from '../../../lib/threadDate'
import type { Message } from '../../../lib/types'

/**
 * Un `.txt` por mensaje del hilo para el ZIP de "Descargar todo": el mensaje actual y los citados,
 * del primero que se envió al último. El nombre lleva número, remitente y fecha; lo que no se pudo
 * leer se dice, sin inventarlo.
 */
export interface MessageText {
  /** Sin extensión: `Mensaje 1 - María - 2026-10-01 09.00`. */
  name: string
  text: string
}

interface Field {
  label: string
  value: string
}

interface Entry {
  fields: Field[]
  body: string
  date: Date | null
}

export const UNKNOWN_SENDER = 'remitente desconocido'
export const UNKNOWN_DATE = 'fecha desconocida'
const NOT_EXTRACTED = 'No se pudo extraer'
const NO_TEXT = 'No se pudo extraer el texto de este mensaje.'
const TRUNCATED = '[El correo es muy largo: el texto se cortó en este punto.]'

const pad = (value: number) => String(value).padStart(2, '0')

function stamp(date: Date): string {
  const day = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  return `${day} ${pad(date.getHours())}.${pad(date.getMinutes())}`
}

const valueOf = (fields: Field[], label: string) =>
  fields.find((field) => field.label === label)?.value.trim()

function currentFields(message: Message): Field[] {
  const recipients = groupRecipients(message.recipients).map((group) => ({
    label: group.label,
    value: group.addresses
      .map((a) => (a.email && a.email !== a.name ? `${a.name} <${a.email}>` : a.name))
      .join('; '),
  }))
  return [
    { label: 'De', value: message.sender ?? '' },
    { label: 'Enviado', value: formatMailDate(message.sent_at) ?? '' },
    ...recipients,
    { label: 'Asunto', value: message.subject ?? '' },
  ]
}

function senderName(entry: Entry): string {
  const raw = valueOf(entry.fields, 'De')
  return (raw && parseAddress(raw).name.slice(0, 60).trim()) || UNKNOWN_SENDER
}

function dateLabel(entry: Entry): string {
  if (entry.date) return stamp(entry.date)
  const raw = valueOf(entry.fields, 'Enviado')
  return raw ? raw.replace(/\s+/g, ' ').slice(0, 40).trim() : UNKNOWN_DATE
}

function fileText(entry: Entry): string {
  const lines = entry.fields
    .filter((field) => field.value.trim() || field.label === 'De' || field.label === 'Enviado')
    .map((field) => `${field.label}: ${field.value.trim() || NOT_EXTRACTED}`)
  return `${lines.join('\n')}\n\n${entry.body.trim() || NO_TEXT}\n`
}

/** Si todos tienen fecha, por fecha; si no, el orden del hilo (el citado más profundo es el primero). */
function chronological(entries: Entry[]): Entry[] {
  if (entries.some((entry) => !entry.date)) return entries
  return [...entries].sort((a, b) => (a.date?.getTime() ?? 0) - (b.date?.getTime() ?? 0))
}

export function messageTexts(message: Message): MessageText[] {
  const thread = splitThread(tidyText(message.body_preview))
  const quoted = thread.quoted.map((item) => ({
    fields: item.fields,
    body: item.body,
    date: parseQuotedDate(valueOf(item.fields, 'Enviado')),
  }))
  const current = { fields: currentFields(message), body: thread.current, date: parseDate(message.sent_at) }
  const inThreadOrder = [current, ...quoted]
  // El corte de un cuerpo largo cae al final del texto: en el mensaje más antiguo.
  if (message.body_truncated) {
    const last = inThreadOrder[inThreadOrder.length - 1]
    last.body = `${last.body.trim()}\n\n${TRUNCATED}`
  }
  const entries = chronological(inThreadOrder.reverse())
  const digits = String(entries.length).length
  return entries.map((entry, index) => ({
    name: `Mensaje ${String(index + 1).padStart(digits, '0')} - ${senderName(entry)} - ${dateLabel(entry)}`,
    text: fileText(entry),
  }))
}
