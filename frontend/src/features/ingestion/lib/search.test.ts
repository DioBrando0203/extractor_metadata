import { describe, expect, it } from 'vitest'
import type { QueueItem } from '../../../lib/types'
import { filterQueue } from './search'

const item = (
  id: string,
  subject: string,
  extra: Partial<NonNullable<QueueItem['message']>> = {},
): QueueItem => ({
  id,
  file: new File(['x'], `${id}.msg`),
  status: 'complete',
  message: {
    file_name: `${id}.msg`,
    file_size_bytes: 1,
    subject,
    recipients: [],
    body_truncated: false,
    headers: [],
    properties: [],
    attachments: [],
    warnings: [],
    status: 'complete',
    ...extra,
  },
})

describe('filterQueue', () => {
  const items = [
    item('a', 'Revisión de planos', { sender: 'María <maria@example.test>' }),
    item('b', 'Factura octubre', { attachments: [{ name: 'Metrado.xlsx', metadata: [], warnings: [] }] }),
  ]

  it('ignora mayúsculas y tildes y exige todas las palabras', () => {
    expect(filterQueue(items, 'REVISION maria').map((entry) => entry.id)).toEqual(['a'])
    expect(filterQueue(items, 'revision factura')).toEqual([])
  })

  it('busca también en nombres de adjuntos y devuelve todo sin consulta', () => {
    expect(filterQueue(items, 'metrado').map((entry) => entry.id)).toEqual(['b'])
    expect(filterQueue(items, '   ')).toBe(items)
  })
})
