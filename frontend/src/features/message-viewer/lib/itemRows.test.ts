import { describe, expect, it } from 'vitest'
import { formatDay, formatWhen } from '../../../lib/formatters'
import type { ItemDetails } from '../../../lib/types'
import { itemRows } from './itemRows'

// Fechas sin zona: se interpretan en la hora local, igual que las muestra el navegador.
const START = '2026-10-12T10:00:00'
const END = '2026-10-12T11:30:00'

const meeting: ItemDetails = {
  kind: 'meeting',
  start: START,
  end: END,
  all_day: false,
  location: 'Sala 3',
  fields: [{ group: 'Reunión', label: 'Organizador', value: 'María Fernández' }],
}

describe('formatWhen', () => {
  it('muestra el día una vez cuando empieza y termina el mismo día', () => {
    expect(formatWhen(START, END)).toBe('lunes, 12 de octubre de 2026, 10:00 – 11:30')
  })

  it('repite el día si termina otro día y omite las horas en todo el día', () => {
    expect(formatWhen(START, '2026-10-13T09:00:00')).toBe(
      'lunes, 12 de octubre de 2026, 10:00 – martes, 13 de octubre de 2026, 09:00',
    )
    expect(formatWhen('2026-10-12T00:00:00', '2026-10-13T00:00:00', true)).toBe(
      'lunes, 12 de octubre de 2026 (todo el día)',
    )
    expect(formatWhen('2026-10-12T00:00:00', '2026-10-14T00:00:00', true)).toBe(
      'lunes, 12 de octubre de 2026 – martes, 13 de octubre de 2026 (todo el día)',
    )
  })

  it('sin inicio no inventa una fecha', () => {
    expect(formatWhen(null, END)).toBeNull()
    expect(formatDay('no es fecha')).toBeNull()
  })
})

describe('itemRows', () => {
  it('ordena cuándo, dónde y los datos del elemento', () => {
    expect(itemRows(meeting)).toEqual([
      { label: 'Cuándo', value: 'lunes, 12 de octubre de 2026, 10:00 – 11:30' },
      { label: 'Dónde', value: 'Sala 3' },
      { label: 'Organizador', value: 'María Fernández' },
    ])
  })

  it('una tarea muestra su vencimiento y omite lo que falta', () => {
    const task: ItemDetails = { kind: 'task', end: END, all_day: false, fields: [] }
    expect(itemRows(task)).toEqual([{ label: 'Vence', value: 'lunes, 12 de octubre de 2026' }])
  })
})
