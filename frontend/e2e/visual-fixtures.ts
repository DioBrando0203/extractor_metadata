import { deflateSync } from 'node:zlib'

/*
 * Datos sintéticos para la revisión visual: correos inventados y miniaturas PNG generadas aquí mismo.
 * Nunca correos reales (regla C-06).
 */

type Rgb = [number, number, number]

function crc32(bytes: Buffer): number {
  let crc = ~0
  for (const byte of bytes) {
    crc ^= byte
    for (let bit = 0; bit < 8; bit++) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1))
  }
  return ~crc >>> 0
}

function chunk(type: string, data: Buffer): Buffer {
  const body = Buffer.concat([Buffer.from(type, 'ascii'), data])
  const length = Buffer.alloc(4)
  length.writeUInt32BE(data.length)
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(body))
  return Buffer.concat([length, body, crc])
}

/** PNG RGB de 8 bits a partir de una función de color por píxel. */
export function png(width: number, height: number, pixel: (x: number, y: number) => Rgb): Buffer {
  const header = Buffer.alloc(13)
  header.writeUInt32BE(width, 0)
  header.writeUInt32BE(height, 4)
  header.set([8, 2, 0, 0, 0], 8)
  const rows = Buffer.alloc((width * 3 + 1) * height)
  for (let y = 0; y < height; y++) {
    const offset = y * (width * 3 + 1)
    for (let x = 0; x < width; x++) rows.set(pixel(x, y), offset + 1 + x * 3)
  }
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', header),
    chunk('IDAT', deflateSync(rows)),
    chunk('IEND', Buffer.alloc(0)),
  ])
}

const dataUri = (image: Buffer) => `data:image/png;base64,${image.toString('base64')}`

/** Paisaje: cielo en degradado, cerro y suelo. */
export const PHOTO = png(480, 300, (x, y) => {
  const hill = 190 - 40 * Math.sin(x / 70)
  if (y < hill) return [40 + y / 3, 110 + y / 4, 200 - y / 6]
  return y < 230 ? [60, 130 - (y - hill) / 3, 70] : [150, 120, 90]
})

/** Miniatura de plano: líneas azules sobre blanco, como las que guarda AutoCAD. */
export const DRAWING = png(320, 200, (x, y) => {
  const line =
    x % 40 === 0 ||
    y % 40 === 0 ||
    Math.abs(x - y * 1.6) < 1.2 ||
    (x > 80 && x < 240 && (y === 60 || y === 140))
  return line ? [15, 108, 189] : [255, 255, 255]
})

/** Portada de presentación: banda de color y bloques de texto. */
export const SLIDE = png(320, 180, (x, y) => {
  if (y < 46) return [202, 80, 16]
  return y > 70 && y < 80 && x > 24 && x < 240 ? [66, 66, 66] : [250, 250, 250]
})

const attachment = (name: string, size_bytes: number, extra: Record<string, unknown> = {}) => ({
  name,
  content_type: null,
  size_bytes,
  metadata: [
    { group: 'Archivo', label: 'Firma detectada', value: name.split('.').pop()?.toUpperCase() ?? '' },
  ],
  warnings: [],
  ...extra,
})

const SHAREPOINT =
  'https://contoso.sharepoint.example.test/sites/obra-24-123/Documentos%20compartidos/Presupuesto%20obra.xlsx'

/** Correo reenviado como adjunto, con asunto largo y su propio adjunto. */
const ATTACHED = {
  file_name: 'Cotización de acero corrugado.msg',
  file_size_bytes: 182_000,
  subject: 'Cotización de acero corrugado para la obra 24-123, válida hasta el 30 de octubre',
  sender: 'Ventas Aceros del Sur <ventas@aceros.example.test>',
  recipients: ['Para: María Fernández <maria.fernandez@example.test>'],
  sent_at: '2026-10-01T11:20:00-05:00',
  body_preview: [
    'Estimada María:',
    '',
    'Adjuntamos la cotización solicitada para el acero corrugado de la obra.',
    '',
    'Saludos,',
    'Ventas',
  ].join(String.fromCharCode(13, 10)),
  body_truncated: false,
  status: 'complete',
  headers: [],
  properties: [],
  attachments: [attachment('Cotización 0923.pdf', 245_000)],
  warnings: [],
}

export const COMPLETE = {
  file_name: 'Revision planos.msg',
  file_size_bytes: 4_812_331,
  subject: 'RE: Proyecto 24-123 | Revisión de planos estructurales y memoria de cálculo actualizada',
  sender: 'María Fernández <maria.fernandez@example.test>',
  recipients: [
    `Para: ${Array.from({ length: 12 }, (_, i) => `Persona ${i + 1} <persona${i + 1}@example.test>`).join('; ')}`,
    'CC: Lucía Torres <lucia.torres@example.test>; Jorge Medina <jorge.medina@example.test>',
  ],
  sent_at: '2026-10-05T15:42:00-05:00',
  body_preview: [
    'Hola equipo,',
    '',
    'Adjunto la revisión 3 de los planos. Así quedó el frente de la obra esta mañana:',
    '[cid:foto-obra@01DA]',
    'Los cambios principales están en las láminas S-201 a S-204.',
    '',
    'Saludos,',
    'María',
    '',
    '________________________________',
    'From: Carlos Rojas <carlos.rojas@example.test>',
    'Sent: Friday, October 2, 2026 6:10 PM',
    'To: María Fernández <maria.fernandez@example.test>',
    'Cc: Equipo de Ingeniería <ingenieria@example.test>',
    'Subject: Proyecto 24-123 | Revisión de planos estructurales',
    '',
    'María, ¿nos puedes enviar la última versión de los planos y la memoria?',
    '',
    '-----Mensaje original-----',
    'De: Lucía Torres',
    'Enviado: jueves, 1 de octubre de 2026 9:00',
    'Para: Carlos Rojas',
    'Asunto: Proyecto 24-123',
    '',
    'Carlos, el cliente pide la revisión antes del viernes.',
  ].join(String.fromCharCode(13, 10)),
  body_truncated: true,
  status: 'complete',
  headers: [],
  properties: [],
  attachments: [
    attachment('Foto obra frontal.png', 1_245_000, {
      preview: dataUri(PHOTO),
      preview_source: 'image',
      content_id: 'foto-obra@01DA',
    }),
    attachment('Modelo estructural.dwg', 2_310_442, {
      preview: dataUri(DRAWING),
      preview_source: 'embedded',
      metadata: [
        { group: 'AutoCAD', label: 'Versión de formato', value: 'DWG 2018 (formato)' },
        { group: 'AutoCAD', label: 'Miniatura incrustada', value: 'Sí' },
      ],
    }),
    attachment('Presentación avance.pptx', 3_120_000, {
      preview: dataUri(SLIDE),
      preview_source: 'embedded',
    }),
    attachment('Cotización de acero corrugado', 182_000, {
      kind: 'message',
      content_type: 'application/vnd.ms-outlook',
      message: ATTACHED,
      metadata: [],
    }),
    attachment('Presupuesto obra.xlsx', 0, {
      kind: 'link',
      size_bytes: null,
      link: SHAREPOINT,
      metadata: [{ group: 'Enlace', label: 'Ubicación', value: SHAREPOINT }],
    }),
    attachment('S-201 Vigas eje C rev3.pdf', 1_245_000),
    attachment('Memoria de cálculo v3.docx', 412_330),
    attachment('Metrado acero.xlsx', 88_120),
    attachment('Fotos obra.zip', 5_400_000),
    attachment('adjunto', 2048, { content_type: 'application/pdf' }),
  ],
  warnings: [],
}

export const PARTIAL = {
  ...COMPLETE,
  file_name: 'RE_ Proyecto 24-123 _ Archivo con nombre muy largo guardado desde el cliente de correo.msg',
  subject: null,
  sender: null,
  recipients: [],
  sent_at: null,
  body_truncated: false,
  status: 'partial',
}

/** Convocatoria de reunión con lugar, asistentes y repetición. */
export const MEETING = {
  ...COMPLETE,
  file_name: 'Reunion semanal.msg',
  subject: 'Revisión semanal de avance de obra',
  recipients: ['Para: Equipo de Ingeniería <ingenieria@example.test>'],
  body_preview: 'Revisaremos el avance de estructuras y el cronograma de vaciado.',
  body_truncated: false,
  attachments: [],
  item: {
    kind: 'meeting',
    start: '2026-10-12T10:00:00',
    end: '2026-10-12T11:30:00',
    all_day: false,
    location: 'Sala Pacífico, piso 2 (y por Teams)',
    fields: [
      { group: 'Reunión', label: 'Organizador', value: 'María Fernández' },
      {
        group: 'Reunión',
        label: 'Obligatorios',
        value: 'Lucía Torres; Jorge Medina; Carlos Rojas; Persona 4; Persona 5; Persona 6',
      },
      { group: 'Reunión', label: 'Opcionales', value: 'Ana Pérez' },
      { group: 'Reunión', label: 'Repetición', value: 'Cada semana el lunes de 10:00 a 11:30' },
    ],
  },
}
