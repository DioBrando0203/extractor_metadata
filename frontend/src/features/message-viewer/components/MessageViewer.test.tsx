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

const file = new File(['correo de prueba'], 'correo.msg', { type: 'application/vnd.ms-outlook' })

describe('MessageViewer', () => {
  it('expone pestanas accesibles y cambia al cuerpo', () => {
    render(<MessageViewer message={message} file={file} onChoose={vi.fn()} />)
    fireEvent.click(screen.getByRole('tab', { name: 'Cuerpo' }))
    expect(screen.getByRole('tabpanel')).toHaveTextContent('Contenido seguro como texto.')
    expect(screen.getByRole('tab', { name: 'Cuerpo' })).toHaveAttribute('aria-selected', 'true')
  })

  it('permite solicitar un nuevo analisis', () => {
    const onChoose = vi.fn()
    render(<MessageViewer message={message} file={file} onChoose={onChoose} />)
    fireEvent.click(screen.getByRole('button', { name: /nuevo analisis/i }))
    expect(onChoose).toHaveBeenCalledOnce()
  })

  it('no muestra diagnosticos tecnicos en la vista principal', () => {
    render(<MessageViewer message={message} file={file} onChoose={vi.fn()} />)
    expect(screen.queryByText(/observaciones del extractor/i)).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: /metadatos/i })).not.toBeInTheDocument()
  })
})
