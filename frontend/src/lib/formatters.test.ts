import { expect, test } from 'vitest'
import { formatBytes, formatDate } from './formatters'

test('muestra bytes vacíos y MB grandes con unidades legibles', () => {
  expect(formatBytes(0)).toBe('0 B')
  expect(formatBytes(11 * 1024 * 1024)).toBe('11 MB')
  expect(formatBytes(null)).toBe('—')
})

test('una fecha faltante o inválida no rompe la vista', () => {
  expect(formatDate(null)).toBe('Sin fecha')
  expect(formatDate('fecha corrupta')).toBe('Sin fecha')
})
