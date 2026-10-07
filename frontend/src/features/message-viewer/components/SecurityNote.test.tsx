import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { Message } from '../../../lib/types'
import { MessageViewer } from './MessageViewer'

const mail: Message = {
  file_name: 'firmado.msg',
  file_size_bytes: 10,
  subject: 'Contrato',
  sender: 'Legal <legal@example.test>',
  recipients: [],
  body_preview: 'Texto firmado del contrato.',
  body_truncated: false,
  headers: [],
  properties: [],
  attachments: [],
  warnings: [],
  status: 'complete',
}
const file = new File(['msg'], 'firmado.msg')
const renderMail = (security: Message['security']) =>
  render(<MessageViewer message={{ ...mail, security }} file={file} />)

describe('SecurityNote', () => {
  it('dice que el correo está firmado sin afirmar que la firma sea válida', () => {
    renderMail('signed')
    expect(screen.getByText('Firmado digitalmente.')).toBeInTheDocument()
    expect(screen.getByText(/no comprueba la firma/)).toBeInTheDocument()
  })

  it('explica por qué no se ve un correo cifrado u opaco', () => {
    renderMail('encrypted')
    expect(screen.getByRole('status')).toHaveTextContent(/Correo cifrado\..*clave del destinatario/)
  })

  it('un correo opaco indica cómo verlo', () => {
    renderMail('opaque')
    expect(screen.getByRole('status')).toHaveTextContent(/formato opaco.*ábrelo con Outlook/)
  })

  it('un correo con permisos dice dónde se puede abrir', () => {
    renderMail('protected')
    expect(screen.getByRole('status')).toHaveTextContent(/Correo con permisos\..*cuenta autorizada/)
  })

  it('un correo normal no muestra aviso de seguridad', () => {
    renderMail(null)
    expect(screen.queryByText(/Firmado digitalmente/)).not.toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })
})
