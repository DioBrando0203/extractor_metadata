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

  it('reduce bloques de líneas vacías del cuerpo sin alterar el texto', () => {
    renderViewer()
    expect(screen.getByText(/Contenido seguro/).textContent).toBe('Contenido seguro como texto.\n\nFirma')
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

  it('no muestra diagnosticos tecnicos en la vista principal', () => {
    renderViewer({ warnings: ['Un campo no fue recuperado'] })
    expect(screen.queryByText(/observaciones del extractor/i)).not.toBeInTheDocument()
    expect(screen.queryByText('Message-ID')).not.toBeInTheDocument()
    expect(screen.queryByText('Un campo no fue recuperado')).not.toBeInTheDocument()
  })
})
