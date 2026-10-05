import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { MessageViewer } from './MessageViewer'

const message = {
  file_name: 'correo.msg',
  file_size_bytes: 40,
  subject: 'Asunto de prueba',
  sender: 'ana@example.test',
  recipients: ['equipo@example.test'],
  sent_at: null,
  body_preview: 'Contenido seguro como texto.',
  body_truncated: false,
  status: 'partial' as const,
  headers: [{ group: 'Encabezado', label: 'Message-ID', value: '<uno>' }],
  properties: [{ group: 'Propiedad', label: 'Clase', value: 'IPM.Note' }],
  attachments: [],
  warnings: ['Un campo no fue recuperado'],
}

describe('MessageViewer', () => {
  it('expone pestañas accesibles y cambia a encabezados', () => {
    render(<MessageViewer message={message} onChoose={vi.fn()} />)
    fireEvent.click(screen.getByRole('tab', { name: 'Encabezados' }))
    expect(screen.getByRole('tabpanel')).toHaveTextContent('Message-ID')
    expect(screen.getByRole('tab', { name: 'Encabezados' })).toHaveAttribute('aria-selected', 'true')
  })

  it('permite solicitar un nuevo análisis', () => {
    const onChoose = vi.fn()
    render(<MessageViewer message={message} onChoose={onChoose} />)
    fireEvent.click(screen.getByRole('button', { name: /nuevo análisis/i }))
    expect(onChoose).toHaveBeenCalledOnce()
  })
})
