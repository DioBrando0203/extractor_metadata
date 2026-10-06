import { describe, expect, it } from 'vitest'
import {
  findInlineAttachment,
  inferSubject,
  inlineAttachmentIndices,
  parseInline,
  splitThread,
} from './thread'

const attachment = (name: string, content_id: string | null = null) => ({
  name,
  content_id,
  metadata: [],
  warnings: [],
})

const REPLY = [
  'Gracias, lo reviso.',
  '',
  '________________________________',
  'From: Carlos Rojas <carlos@example.test>',
  'Sent: Friday, October 2, 2026 6:10 PM',
  'To: María <maria@example.test>; Equipo',
  '    <equipo@example.test>',
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

describe('splitThread', () => {
  it('separa el mensaje actual de los citados en inglés y en español', () => {
    const thread = splitThread(REPLY)
    expect(thread.current).toBe('Gracias, lo reviso.')
    expect(thread.quoted).toHaveLength(2)
    expect(thread.quoted[0].fields.map((field) => field.label)).toEqual(['De', 'Enviado', 'Para', 'Asunto'])
    expect(thread.quoted[0].fields[2].value).toBe('María <maria@example.test>; Equipo <equipo@example.test>')
    expect(thread.quoted[0].body).toBe('Envío la revisión.')
    expect(thread.quoted[1].fields[0]).toEqual({ label: 'De', value: 'María' })
    expect(thread.quoted[1].body).toBe('¿Me envías los planos?')
  })

  it('no confunde una línea "De:" suelta con un mensaje citado', () => {
    const text = 'De: acuerdo con lo hablado\nseguimos mañana.'
    expect(splitThread(text)).toEqual({ current: text, quoted: [] })
  })
})

describe('imágenes incrustadas', () => {
  it('parte el texto en el orden de aparición', () => {
    expect(parseInline('Hola\n[cid:image001.png@01DA]\nFirma')).toEqual([
      { kind: 'text', text: 'Hola' },
      { kind: 'image', cid: 'image001.png@01DA' },
      { kind: 'text', text: 'Firma' },
    ])
  })

  it('empareja por Content-ID y, si falta, por nombre de archivo', () => {
    const attachments = [
      attachment('plano.pdf'),
      attachment('logo.png', 'abc@01'),
      attachment('image002.jpg'),
    ]
    expect(findInlineAttachment('ABC@01', attachments)).toBe(1)
    expect(findInlineAttachment('image002.jpg@01DA', attachments)).toBe(2)
    expect(findInlineAttachment('otra.png@x', attachments)).toBe(-1)
    expect([...inlineAttachmentIndices('a [cid:abc@01] b [cid:image002.jpg@x]', attachments)]).toEqual([1, 2])
  })
})

describe('inferSubject', () => {
  it('sólo acepta el asunto citado si reproduce el nombre del archivo con las reglas de Outlook', () => {
    const quoted = splitThread(REPLY).quoted
    expect(inferSubject('RE_ Planos rev3', quoted)).toBe('RE: Planos rev3')
    expect(inferSubject('Planos rev4', quoted)).toBeNull()
    expect(inferSubject('RE_ Planos rev3', [])).toBeNull()
  })
})
