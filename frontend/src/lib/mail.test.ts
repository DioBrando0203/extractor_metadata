import { describe, expect, it } from 'vitest'
import {
  groupRecipients,
  messageTitle,
  messageTrail,
  parseAddress,
  previewLine,
  splitAddresses,
} from './mail'
import type { Message } from './types'

describe('parseAddress', () => {
  it('separa nombre y correo en formato con corchetes angulares', () => {
    expect(parseAddress('"Ana Pérez" <ana@example.test>')).toEqual({
      name: 'Ana Pérez',
      email: 'ana@example.test',
    })
  })

  it('usa el correo como nombre cuando sólo hay dirección y conserva nombres sin correo', () => {
    expect(parseAddress('ana@example.test')).toEqual({ name: 'ana@example.test', email: 'ana@example.test' })
    expect(parseAddress('Ana Pérez')).toEqual({ name: 'Ana Pérez', email: null })
  })
})

describe('splitAddresses', () => {
  it('no parte nombres con coma y sí separa direcciones completas por coma o punto y coma', () => {
    expect(
      splitAddresses('Pérez, Ana <ana@example.test>, luis@example.test; Equipo').map((a) => a.name),
    ).toEqual(['Pérez, Ana', 'luis@example.test', 'Equipo'])
  })
})

describe('groupRecipients', () => {
  it('agrupa por prefijo en el orden Para, CC, CCO y trata líneas sin prefijo como Para', () => {
    const groups = groupRecipients([
      'CCO: oculto@example.test',
      'CC: copia@example.test',
      'equipo@example.test',
    ])
    expect(groups.map((group) => group.label)).toEqual(['Para', 'CC', 'CCO'])
  })

  it('omite grupos vacíos', () => {
    expect(groupRecipients(['CC: ', 'Para: ;'])).toEqual([])
  })
})

describe('messageTitle y previewLine', () => {
  it('cae al nombre del archivo sin extensión cuando no hay asunto', () => {
    expect(messageTitle('  ', 'RE_ Informe.MSG')).toEqual({ text: 'RE_ Informe', source: 'file' })
    expect(messageTitle('Hola', 'x.msg')).toEqual({ text: 'Hola', source: 'subject' })
  })

  it('deduce el asunto del mensaje citado sólo si reproduce el nombre del archivo', () => {
    const body = [
      'Gracias.',
      '',
      'From: Carlos <c@example.test>',
      'Sent: lunes',
      'Subject: KMV-24 | Martin County',
      '',
      'Hola',
    ].join('\n')
    expect(messageTitle(null, 'RE_ KMV-24 _ Martin County.msg', body)).toEqual({
      text: 'RE: KMV-24 | Martin County',
      source: 'inferred',
    })
    expect(messageTitle(null, 'Otro nombre.msg', body)).toEqual({ text: 'Otro nombre', source: 'file' })
  })

  it('resume el cuerpo en una línea', () => {
    expect(previewLine('Hola\n\n  equipo,\tgracias', 12)).toBe('Hola equipo,')
    expect(previewLine(null)).toBe('')
  })
})

describe('messageTrail', () => {
  const mail = (subject: string, attachments: Message['attachments'] = []): Message => ({
    file_name: `${subject}.msg`,
    file_size_bytes: 1,
    subject,
    recipients: [],
    body_truncated: false,
    headers: [],
    properties: [],
    attachments,
    warnings: [],
    status: 'complete',
  })
  const attached = (message: Message | null) => ({
    name: message?.subject ?? 'roto',
    metadata: [],
    warnings: [],
    kind: 'message' as const,
    message,
  })
  const root = mail('Principal', [
    { name: 'plano.dwg', metadata: [], warnings: [] },
    attached(mail('Nivel 1', [attached(mail('Nivel 2')), attached(null)])),
  ])

  it('sigue la ruta de correos adjuntos desde el principal', () => {
    expect(messageTrail(root, []).map((item) => item.subject)).toEqual(['Principal'])
    expect(messageTrail(root, [1, 0]).map((item) => item.subject)).toEqual([
      'Principal',
      'Nivel 1',
      'Nivel 2',
    ])
  })

  it('se corta donde la ruta no lleva a un correo leído', () => {
    expect(messageTrail(root, [0]).map((item) => item.subject)).toEqual(['Principal'])
    expect(messageTrail(root, [1, 1]).map((item) => item.subject)).toEqual(['Principal', 'Nivel 1'])
    expect(messageTrail(root, [7]).map((item) => item.subject)).toEqual(['Principal'])
  })
})
