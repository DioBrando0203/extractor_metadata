import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Message } from '../../../lib/types'
import { HighlightContext } from '../highlight'
import { MessageViewer } from './MessageViewer'

const invitation: Message = {
  file_name: 'reunion.msg',
  file_size_bytes: 10,
  subject: 'Revisión de planos',
  sender: 'María Fernández <maria@example.test>',
  recipients: [],
  body_preview: 'Revisemos las láminas S-201 a S-204.',
  body_truncated: false,
  headers: [],
  properties: [],
  attachments: [],
  warnings: [],
  status: 'complete',
  item: {
    kind: 'cancellation',
    start: '2026-10-12T10:00:00',
    end: '2026-10-12T11:30:00',
    all_day: false,
    location: 'Sala 3, piso 2',
    fields: [{ group: 'Reunión', label: 'Obligatorios', value: 'Ana Pérez; Luis Rojas' }],
  },
}
const file = new File(['msg'], 'reunion.msg')

describe('ItemCard', () => {
  it('muestra qué es, cuándo, dónde y quiénes antes del texto', () => {
    render(<MessageViewer message={invitation} file={file} />)
    const card = screen.getByRole('region', { name: 'Reunión cancelada' })
    const rows = within(card)
      .getAllByRole('term')
      .map((term) => [term.textContent, term.nextElementSibling?.textContent])
    expect(rows).toEqual([
      ['Cuándo', 'lunes, 12 de octubre de 2026, 10:00 – 11:30'],
      ['Dónde', 'Sala 3, piso 2'],
      ['Obligatorios', 'Ana Pérez; Luis Rojas'],
    ])
  })

  it('resalta y cuenta la búsqueda dentro de la tarjeta', () => {
    render(
      <HighlightContext.Provider value={['sala']}>
        <MessageViewer message={invitation} file={file} terms={['sala']} />
      </HighlightContext.Provider>,
    )
    const card = screen.getByRole('region', { name: 'Reunión cancelada' })
    expect(within(card).getByText('Sala').tagName).toBe('MARK')
    expect(screen.getByText(/1 coincidencia/)).toBeInTheDocument()
  })

  it('un correo normal no muestra tarjeta', () => {
    render(<MessageViewer message={{ ...invitation, item: null }} file={file} />)
    expect(screen.queryByRole('region', { name: 'Reunión cancelada' })).not.toBeInTheDocument()
  })
})
