/**
 * Fecha del campo "Enviado" de un mensaje citado, escrita por Outlook como texto libre en español o en
 * inglés: `jueves, 1 de octubre de 2026 9:00`, `Friday, October 2, 2026 6:10 PM` o `01/10/2026 9:00`.
 * Función pura: devuelve `null` si no reconoce el formato, sin adivinar.
 */

const MONTHS: Record<string, number> = {
  enero: 1,
  febrero: 2,
  marzo: 3,
  abril: 4,
  mayo: 5,
  junio: 6,
  julio: 7,
  agosto: 8,
  septiembre: 9,
  setiembre: 9,
  octubre: 10,
  noviembre: 11,
  diciembre: 12,
  january: 1,
  february: 2,
  march: 3,
  april: 4,
  may: 5,
  june: 6,
  july: 7,
  august: 8,
  september: 9,
  october: 10,
  november: 11,
  december: 12,
}
const DAY_MONTH_YEAR = /(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})/i
const MONTH_DAY_YEAR = /([a-z]+)\s+(\d{1,2}),?\s+(\d{4})/i
const NUMERIC = /(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})/
const TIME = /(\d{1,2}):(\d{2})(?::\d{2})?\s*(a\.?\s*m\.?|p\.?\s*m\.?)?/i

function datePart(text: string): [number, number, number] | null {
  const spanish = text.match(DAY_MONTH_YEAR)
  if (spanish && MONTHS[spanish[2].toLowerCase()])
    return [Number(spanish[3]), MONTHS[spanish[2].toLowerCase()], Number(spanish[1])]
  const english = text.match(MONTH_DAY_YEAR)
  if (english && MONTHS[english[1].toLowerCase()])
    return [Number(english[3]), MONTHS[english[1].toLowerCase()], Number(english[2])]
  // Numérica: día primero, como la escribe Outlook en español.
  const numeric = text.match(NUMERIC)
  return numeric ? [Number(numeric[3]), Number(numeric[2]), Number(numeric[1])] : null
}

function timePart(text: string): [number, number] {
  const match = text.match(TIME)
  if (!match) return [0, 0]
  let hours = Number(match[1])
  const meridiem = match[3]?.toLowerCase().replace(/[.\s]/g, '')
  if (meridiem === 'pm' && hours < 12) hours += 12
  if (meridiem === 'am' && hours === 12) hours = 0
  return [hours, Number(match[2])]
}

/** Fecha local del texto citado o `null` si no se reconoce. */
export function parseQuotedDate(text?: string | null): Date | null {
  if (!text) return null
  const day = datePart(text)
  if (!day) return null
  const [year, month, date] = day
  const [hours, minutes] = timePart(text.slice(text.search(/\d{4}/) + 4))
  const result = new Date(year, month - 1, date, hours, minutes)
  const valid = result.getMonth() === month - 1 && result.getDate() === date && hours < 24 && minutes < 60
  return valid ? result : null
}
