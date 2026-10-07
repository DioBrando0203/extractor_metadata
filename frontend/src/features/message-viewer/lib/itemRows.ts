import { formatDay, formatWhen } from '../../../lib/formatters'
import type { ItemDetails, ItemKind } from '../../../lib/types'

export const ITEM_TITLES: Record<ItemKind, string> = {
  meeting: 'Invitación a una reunión',
  cancellation: 'Reunión cancelada',
  response: 'Respuesta a una reunión',
  appointment: 'Cita',
  contact: 'Contacto',
  task: 'Tarea',
}

export type ItemRow = { label: string; value: string }

/** Filas de la tarjeta en orden de lectura: cuándo, dónde y después los datos del backend. */
export function itemRows(item: ItemDetails): ItemRow[] {
  const rows: (ItemRow | null)[] =
    item.kind === 'task'
      ? [row('Inicio', formatDay(item.start)), row('Vence', formatDay(item.end))]
      : [row('Cuándo', formatWhen(item.start, item.end, item.all_day))]
  rows.push(row('Dónde', item.location), ...item.fields.map((field) => row(field.label, field.value)))
  return rows.filter((entry): entry is ItemRow => entry !== null)
}

function row(label: string, value: string | null | undefined): ItemRow | null {
  return value ? { label, value } : null
}
