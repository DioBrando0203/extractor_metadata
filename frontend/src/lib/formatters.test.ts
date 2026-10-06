import { describe, expect, test } from 'vitest'
import { formatBytes, formatDate, formatListDate, formatMailDate, tidyText } from './formatters'

test('muestra bytes vacíos y MB grandes con unidades legibles', () => {
  expect(formatBytes(0)).toBe('0 B')
  expect(formatBytes(11 * 1024 * 1024)).toBe('11 MB')
  expect(formatBytes(null)).toBe('—')
})

test('una fecha faltante o inválida no rompe la vista', () => {
  expect(formatDate(null)).toBe('Sin fecha')
  expect(formatDate('fecha corrupta')).toBe('Sin fecha')
  expect(formatMailDate(null)).toBeNull()
  expect(formatMailDate('fecha corrupta')).toBeNull()
  expect(formatListDate(undefined)).toBeNull()
})

describe('formatListDate', () => {
  const now = new Date(2026, 9, 5, 21, 0)

  test('muestra sólo la hora para correos de hoy', () => {
    expect(formatListDate(new Date(2026, 9, 5, 8, 7).toISOString(), now)).toBe('08:07')
  })

  test('muestra día y mes en el año actual y fecha corta en años anteriores', () => {
    expect(formatListDate(new Date(2026, 2, 14, 9, 0).toISOString(), now)).toMatch(/^14 mar/)
    expect(formatListDate(new Date(2024, 6, 1, 9, 0).toISOString(), now)).toBe('01/07/24')
  })
})

test('formatMailDate usa reloj de 24 horas e incluye el día de la semana', () => {
  expect(formatMailDate(new Date(2026, 9, 5, 20, 13).toISOString())).toMatch(/^lun.* 05\/10\/2026.* 20:13$/)
})

test('tidyText normaliza saltos y espacios sin cambiar el contenido', () => {
  expect(tidyText('Hola  \r\n\r\n\r\n\r\nequipo\t\n')).toBe('Hola\n\nequipo')
  expect(tidyText(null)).toBe('')
})
