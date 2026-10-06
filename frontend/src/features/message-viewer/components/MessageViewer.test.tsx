import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Message } from '../../../lib/types'
import { MessageViewer } from './MessageViewer'

const base: Message = {
  file_name: 'correo.msg',
  file_size_bytes: 40,
  subject: 'Asunto de prueba',
  sender: 'Ana Pérez <ana@example.test>',
  recipients: ['Para: Equipo <equipo@example.test>; Luis <luis@example.test>', 'CC: copia@example.test'],
  sent_at: '2026-10-05T20:13:00-05:00',
  body_preview: 'Contenido seguro como texto.\n\n\n\nFirma',
  body_truncated: false,
  status: 'complete',
  headers: [{ group: 'Encabezado', label: 'Message-ID', value: '<uno>' }],
  properties: [{ group: 'Propiedad', label: 'Clase', value: 'IPM.Note' }],
  attachments: [
    { name: 'plano.dwg', content_type: 'image/vnd.dwg', size_bytes: 2048, metadata: [], warnings: [] },
  ],
  warnings: [],
}

const file = new File(['correo de prueba'], 'correo.msg', { type: 'application/vnd.ms-outlook' })
const renderViewer = (overrides: Partial<Message> = {}) =>
  render(<MessageViewer message={{ ...base, ...overrides }} file={file} />)

describe('MessageViewer', () => {
  it('muestra encabezado, adjuntos y cuerpo en una sola vista, sin pestañas', () => {
    renderViewer()
    expect(screen.getByRole('heading', { level: 1, name: 'Asunto de prueba' })).toBeInTheDocument()
    expect(screen.getByText('Ana Pérez')).toBeInTheDocument()
    expect(screen.getByText('<ana@example.test>')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Descargar plano.dwg' })).toBeInTheDocument()
    expect(screen.getByText(/Contenido seguro como texto/)).toBeInTheDocument()
    expect(screen.queryByRole('tab')).not.toBeInTheDocument()
  })

  it('agrupa destinatarios por Para y CC con el nombre visible y el correo como título', () => {
    renderViewer()
    const rows = screen.getAllByRole('term').map((term) => term.textContent)
    expect(rows).toEqual(['Para:', 'CC:'])
    expect(screen.getByText(/Luis/)).toHaveAttribute('title', 'luis@example.test')
  })

  it('pliega listas largas de destinatarios y permite verlas todas', () => {
    const many = Array.from({ length: 10 }, (_, index) => `Persona ${index + 1} <p${index + 1}@example.test>`)
    renderViewer({ recipients: [`Para: ${many.join('; ')}`] })
    expect(screen.queryByText(/Persona 9/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /^\+2 más/ }))
    expect(screen.getByText(/Persona 10/)).toBeInTheDocument()
  })

  it('convierte bloques de líneas vacías en párrafos sin alterar el texto', () => {
    renderViewer()
    const paragraphs = screen.getByRole('region', { name: 'Contenido del correo' }).querySelectorAll('p')
    expect([...paragraphs].map((paragraph) => paragraph.textContent)).toEqual([
      'Contenido seguro como texto.',
      'Firma',
    ])
  })

  it('usa el nombre del archivo cuando falta el asunto y lo indica', () => {
    renderViewer({ subject: null, file_name: 'RE_ Informe semanal.msg' })
    expect(screen.getByRole('heading', { level: 1, name: 'RE_ Informe semanal' })).toBeInTheDocument()
    expect(screen.getByText(/Asunto no recuperado/)).toBeInTheDocument()
  })

  it('en lectura parcial avisa sin inventar remitente, destinatarios ni fecha', () => {
    renderViewer({ status: 'partial', sender: null, recipients: [], sent_at: null })
    expect(screen.getByText('Lectura parcial.')).toBeInTheDocument()
    expect(screen.getByText('Remitente desconocido')).toBeInTheDocument()
    expect(screen.queryByRole('term')).not.toBeInTheDocument()
    expect(screen.queryByText('Sin fecha')).not.toBeInTheDocument()
  })

  it('pliega listas largas de adjuntos y permite mostrarlas todas', () => {
    const attachments = Array.from({ length: 9 }, (_, index) => ({
      name: `foto-${index + 1}.png`,
      size_bytes: 10,
      metadata: [],
      warnings: [],
    }))
    renderViewer({ attachments })
    const section = screen.getByRole('region', { name: /9 datos adjuntos/ })
    expect(within(section).getAllByRole('button', { name: /^Descargar/ })).toHaveLength(6)
    fireEvent.click(within(section).getByRole('button', { name: 'Mostrar los 9' }))
    expect(within(section).getAllByRole('button', { name: /^Descargar/ })).toHaveLength(9)
  })

  it('coloca las imágenes incrustadas en su posición y reúne todo en la pestaña de adjuntos', () => {
    const logo = { name: 'logo.png', content_id: 'logo@01', preview: 'data:image/png;base64,iVBORw0KGgo=' }
    renderViewer({
      body_preview: ['Hola equipo', '[cid:logo@01]', 'Saludos'].join('\n'),
      attachments: [
        { ...logo, size_bytes: 10, metadata: [], warnings: [] },
        { name: 'plano.dwg', size_bytes: 20, metadata: [], warnings: [] },
      ],
    })
    const body = screen.getByRole('region', { name: 'Contenido del correo' })
    expect(within(body).getByRole('button', { name: 'Ver logo.png' })).toBeInTheDocument()
    expect(body.textContent?.indexOf('Hola equipo')).toBeLessThan(body.textContent?.indexOf('Saludos') ?? 0)
    expect(screen.getByRole('region', { name: /1 dato adjunto/ })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: 'Datos adjuntos (2)' }))
    expect(screen.getByRole('tab', { name: 'Datos adjuntos (2)' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getAllByRole('button', { name: /^Descargar/ })).toHaveLength(2)
  })

  it('sin imágenes incrustadas no muestra pestañas', () => {
    renderViewer()
    expect(screen.queryByRole('tablist')).not.toBeInTheDocument()
  })

  it('pliega el historial citado e identifica a quién envió cada mensaje', () => {
    renderViewer({
      body_preview: [
        'Gracias.',
        '',
        'From: Carlos Rojas <carlos@example.test>',
        'Sent: Friday, October 2, 2026 6:10 PM',
        'To: Ana',
        'Subject: Planos',
        '',
        'Envío los planos.',
      ].join('\n'),
    })
    expect(screen.queryByText('Envío los planos.')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Mostrar el mensaje anterior' }))
    const quoted = screen.getByRole('article', { name: 'Mensaje de Carlos Rojas' })
    expect(within(quoted).getByText('<carlos@example.test>')).toBeInTheDocument()
    expect(within(quoted).getByText('Friday, October 2, 2026 6:10 PM')).toBeInTheDocument()
    expect(within(quoted).getByText('Envío los planos.')).toBeInTheDocument()
  })

  it('deduce el asunto del mensaje citado cuando coincide con el nombre del archivo', () => {
    renderViewer({
      subject: null,
      file_name: 'RE_ Planos _ rev3.msg',
      body_preview: ['Ok', '', 'De: Carlos', 'Enviado: lunes', 'Asunto: Planos | rev3', '', 'Adjunto'].join(
        '\n',
      ),
    })
    expect(screen.getByRole('heading', { level: 1, name: 'RE: Planos | rev3' })).toBeInTheDocument()
    expect(screen.getByText(/Asunto deducido del mensaje citado/)).toBeInTheDocument()
  })

  it('resalta la búsqueda, cuenta coincidencias y abre el historial si están ahí', () => {
    render(
      <MessageViewer
        message={{
          ...base,
          body_preview: [
            'Gracias.',
            '',
            'From: Carlos',
            'Sent: hoy',
            'Subject: Planos',
            '',
            'Plano de Martin County',
          ].join(String.fromCharCode(10)),
        }}
        file={file}
        terms={['martin']}
      />,
    )
    expect(screen.getByText(/1 coincidencia de la búsqueda/)).toBeInTheDocument()
    expect(screen.getByText('Martin', { selector: 'mark' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ocultar mensajes anteriores' })).toBeInTheDocument()
  })

  it('marca la imagen ubicada por tamaño y avisa de las que no se recuperaron', () => {
    renderViewer({
      body_preview: ['Firma', '[cid:image001.jpg@01DD]', '[cid:image004.png@01DD]'].join(
        String.fromCharCode(10),
      ),
      attachments: [
        {
          name: 'adjunto-1.jpg',
          content_id: 'image001.jpg@01DD',
          content_id_inferred: true,
          preview: 'data:image/png;base64,iVBORw0KGgo=',
          metadata: [],
          warnings: [],
        },
      ],
    })
    expect(screen.getByRole('button', { name: 'Ver adjunto-1.jpg' })).toBeInTheDocument()
    expect(screen.getByText(/^Ubicación reconstruida$/)).toBeInTheDocument()
    expect(screen.getByText(/Imagen no recuperada · image004.png/)).toBeInTheDocument()
  })

  it('no muestra diagnosticos tecnicos en la vista principal', () => {
    renderViewer({ warnings: ['Un campo no fue recuperado'] })
    expect(screen.queryByText(/observaciones del extractor/i)).not.toBeInTheDocument()
    expect(screen.queryByText('Message-ID')).not.toBeInTheDocument()
    expect(screen.queryByText('Un campo no fue recuperado')).not.toBeInTheDocument()
  })
})
