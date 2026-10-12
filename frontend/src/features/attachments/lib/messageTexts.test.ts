import { describe, expect, it } from 'vitest'
import { parseQuotedDate } from '../../../lib/threadDate'
import type { Message } from '../../../lib/types'
import { messageTexts } from './messageTexts'

const BODY = [
  'Gracias, lo reviso.',
  '',
  '________________________________',
  'From: Carlos Rojas <carlos@example.test>',
  'Sent: Friday, October 2, 2026 6:10 PM',
  'To: María <maria@example.test>',
  'Subject: RE: Planos rev3',
  '',
  'Envío la revisión.',
  '',
  '-----Mensaje original-----',
  'De: María',
  'Enviado: jueves, 1 de octubre de 2026 9:00',
  'Para: Carlos Rojas',
  'Asunto: Planos rev3',
  '',
  '¿Me envías los planos?',
].join('\n')

const message = (overrides: Partial<Message> = {}): Message => ({
  file_name: 'RE_ Planos rev3.msg',
  file_size_bytes: 10,
  subject: 'RE: Planos rev3',
  sender: 'Ana Pérez <ana@example.test>',
  recipients: ['Para: Carlos Rojas <carlos@example.test>'],
  sent_at: new Date(2026, 9, 3, 8, 5).toISOString(),
  body_preview: BODY,
  body_truncated: false,
  headers: [],
  properties: [],
  attachments: [],
  warnings: [],
  status: 'complete',
  ...overrides,
})

describe('messageTexts', () => {
  it('ordena del primer mensaje enviado al último con remitente y fecha en el nombre', () => {
    const texts = messageTexts(message())
    expect(texts.map((text) => text.name)).toEqual([
      'Mensaje 1 - María - 2026-10-01 09.00',
      'Mensaje 2 - Carlos Rojas - 2026-10-02 18.10',
      'Mensaje 3 - Ana Pérez - 2026-10-03 08.05',
    ])
    expect(texts[0].text).toContain('De: María\nEnviado: jueves, 1 de octubre de 2026 9:00')
    expect(texts[0].text.trim().endsWith('¿Me envías los planos?')).toBe(true)
    expect(texts[2].text).toContain('Para: Carlos Rojas <carlos@example.test>')
    expect(texts[2].text).toContain('Gracias, lo reviso.')
  })

  it('dice lo que no se pudo extraer en lugar de inventarlo', () => {
    const [only] = messageTexts(message({ sender: null, sent_at: null, subject: null, body_preview: null }))
    expect(only.name).toBe('Mensaje 1 - remitente desconocido - fecha desconocida')
    expect(only.text).toContain('De: No se pudo extraer\nEnviado: No se pudo extraer')
    expect(only.text).toContain('No se pudo extraer el texto de este mensaje.')
  })

  it('avisa del corte de un cuerpo largo en el mensaje más antiguo', () => {
    const texts = messageTexts(message({ body_truncated: true }))
    expect(texts[0].text).toContain('el texto se cortó')
    expect(texts[2].text).not.toContain('el texto se cortó')
  })
})

describe('parseQuotedDate', () => {
  it('lee fechas de Outlook en español, inglés y numéricas', () => {
    expect(parseQuotedDate('jueves, 1 de octubre de 2026 9:00 p. m.')).toEqual(new Date(2026, 9, 1, 21, 0))
    expect(parseQuotedDate('Friday, October 2, 2026 12:10 AM')).toEqual(new Date(2026, 9, 2, 0, 10))
    expect(parseQuotedDate('05/10/2026 20:13')).toEqual(new Date(2026, 9, 5, 20, 13))
    expect(parseQuotedDate('ayer por la tarde')).toBeNull()
    expect(parseQuotedDate('31/02/2026')).toBeNull()
  })
})
