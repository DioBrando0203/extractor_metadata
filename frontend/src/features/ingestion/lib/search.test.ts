import { describe, expect, it } from 'vitest'
import type { QueueItem } from '../../../lib/types'
import { filterQueue, matchPreview } from './search'

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

describe('matchPreview', () => {
  const message = {
    file_name: 'a.msg',
    file_size_bytes: 1,
    subject: 'Asunto',
    recipients: ['Para: Ana <ana@example.test>'],
    body_preview: 'Texto inicial. Más adelante aparece la revisión de planos estructurales.',
    body_truncated: false,
    headers: [],
    properties: [],
    attachments: [{ name: 'Metrado acero.xlsx', metadata: [], warnings: [] }],
    warnings: [],
    status: 'complete' as const,
  }

  it('muestra dónde coincide: texto, adjunto o destinatarios', () => {
    expect(matchPreview(message, ['revision'])).toContain('revisión de planos')
    expect(matchPreview(message, ['metrado'])).toBe('Adjunto: Metrado acero.xlsx')
    expect(matchPreview(message, ['ana@example'])).toContain('ana@example.test')
    expect(matchPreview(message, [])).toBeNull()
  })
})

describe('búsqueda dentro de correos adjuntos', () => {
  const inner = {
    file_name: 'Cotización.msg',
    file_size_bytes: 1,
    subject: 'Cotización de acero',
    sender: 'Proveedor <ventas@acero.example.test>',
    recipients: [],
    body_preview: 'Adjuntamos el precio del acero corrugado para la obra.',
    body_truncated: false,
    headers: [],
    properties: [],
    attachments: [],
    warnings: [],
    status: 'complete' as const,
  }
  const forwarded = item('c', 'Reenvío', {
    body_preview: 'Te reenvío lo del proveedor.',
    attachments: [
      { name: 'Cotización de acero', metadata: [], warnings: [], kind: 'message', message: inner },
    ],
  })
  const outer = {
    ...inner,
    subject: 'Reenvío',
    sender: null,
    body_preview: 'Te reenvío lo del proveedor.',
    attachments: forwarded.message?.attachments ?? [],
  }

  it('encuentra el correo por el texto o el remitente de su correo adjunto', () => {
    expect(filterQueue([forwarded], 'corrugado').map((entry) => entry.id)).toEqual(['c'])
    expect(filterQueue([forwarded], 'ventas@acero').map((entry) => entry.id)).toEqual(['c'])
  })

  it('explica que la coincidencia está en el correo adjunto', () => {
    expect(matchPreview(outer, ['corrugado'])).toMatch(/^Correo adjunto «Cotización de acero»: .*corrugado/)
    expect(matchPreview(outer, ['ventas@acero'])).toBe('Correo adjunto: Cotización de acero')
  })
})

describe('búsqueda en reuniones', () => {
  it('encuentra una reunión por su lugar o sus asistentes', () => {
    const meeting = item('r', 'Revisión semanal', {
      item: {
        kind: 'meeting',
        all_day: false,
        location: 'Sala Pacífico',
        fields: [{ group: 'Reunión', label: 'Obligatorios', value: 'Ana Pérez' }],
      },
    })
    expect(filterQueue([meeting], 'pacifico').map((entry) => entry.id)).toEqual(['r'])
    expect(filterQueue([meeting], 'perez').map((entry) => entry.id)).toEqual(['r'])
  })
})
