import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Attachment, Message } from '../../../lib/types'

const mocks = vi.hoisted(() => ({ fetchAttachment: vi.fn(), saveBlob: vi.fn() }))
vi.mock('../../../lib/api', () => mocks)
import { MessageReader } from './MessageReader'

const SHARE = String.raw`\\servidor\obras\plano.dwg`
const file = new File(['msg'], 'reenvio.msg')
const mail = (subject: string, extra: Partial<Message> = {}): Message => ({
  file_name: `${subject}.msg`,
  file_size_bytes: 100,
  subject,
  recipients: [],
  body_truncated: false,
  headers: [],
  properties: [],
  attachments: [],
  warnings: [],
  status: 'complete',
  ...extra,
})
const attachment = (name: string, extra: Partial<Attachment> = {}): Attachment => ({
  name,
  size_bytes: 900,
  metadata: [],
  warnings: [],
  ...extra,
})
const inner = mail('Cotización de acero', {
  sender: 'Proveedor <ventas@acero.example.test>',
  body_preview: 'Precio del acero corrugado.',
  attachments: [attachment('precio.pdf')],
})
const root = mail('Reenvío', {
  sender: 'Ana <ana@example.test>',
  body_preview: 'Te reenvío lo del proveedor.',
  attachments: [
    attachment('Cotización de acero', { kind: 'message', message: inner }),
    attachment('Presupuesto.xlsx', {
      kind: 'link',
      link: 'https://contoso.sharepoint.com/x',
      size_bytes: null,
    }),
    attachment('plano.dwg', { kind: 'link', link: SHARE, size_bytes: null }),
  ],
})

describe('MessageReader', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:x'), revokeObjectURL: vi.fn() })
    mocks.fetchAttachment.mockResolvedValue({ blob: new Blob(['%PDF']), filename: 'precio.pdf' })
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('abre un correo adjunto como un correo propio y vuelve al que lo contiene', () => {
    render(<MessageReader message={root} file={file} />)
    fireEvent.click(screen.getByRole('button', { name: 'Abrir Cotización de acero' }))

    expect(screen.getByRole('heading', { level: 1, name: 'Cotización de acero' })).toHaveFocus()
    expect(screen.getByText('Proveedor')).toBeInTheDocument()
    expect(screen.getByText('Precio del acero corrugado.')).toBeInTheDocument()
    const trail = screen.getByRole('navigation', { name: 'Correo adjunto' })
    expect(within(trail).getByText('Reenvío')).toBeInTheDocument()

    fireEvent.click(within(trail).getByRole('button', { name: 'Volver a Reenvío' }))
    expect(screen.getByRole('heading', { level: 1, name: 'Reenvío' })).toHaveFocus()
    expect(screen.queryByRole('navigation', { name: 'Correo adjunto' })).not.toBeInTheDocument()
  })

  it('descarga un adjunto del correo adjunto indicando su ruta', async () => {
    render(<MessageReader message={root} file={file} />)
    fireEvent.click(screen.getByRole('button', { name: 'Abrir Cotización de acero' }))
    fireEvent.click(screen.getByRole('button', { name: 'Descargar precio.pdf' }))

    await waitFor(() => expect(mocks.saveBlob).toHaveBeenCalled())
    expect(mocks.fetchAttachment).toHaveBeenCalledWith(file, 0, 'precio.pdf', {
      preview: false,
      messagePath: [0],
    })
  })

  it('un enlace no se descarga y el visor lo abre en otra pestaña sin datos de origen', () => {
    render(<MessageReader message={root} file={file} />)
    expect(screen.queryByRole('button', { name: 'Descargar Presupuesto.xlsx' })).not.toBeInTheDocument()
    expect(screen.getByText('XLSX · Enlace web')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Ver Presupuesto.xlsx' }))
    const dialog = screen.getByRole('dialog', { name: 'Presupuesto.xlsx' })
    const link = within(dialog).getByRole('link', { name: 'Abrir enlace' })
    expect(link).toHaveAttribute('href', 'https://contoso.sharepoint.com/x')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    expect(within(dialog).queryByRole('button', { name: /Descargar/ })).not.toBeInTheDocument()
    expect(within(dialog).getByText(/no viaja dentro del correo/)).toBeInTheDocument()
  })

  it('una ruta de red se muestra como texto, nunca como enlace', () => {
    render(<MessageReader message={root} file={file} />)
    fireEvent.click(screen.getByRole('button', { name: 'Ver plano.dwg' }))
    const dialog = screen.getByRole('dialog', { name: 'plano.dwg' })
    expect(within(dialog).getByText(SHARE)).toBeInTheDocument()
    expect(within(dialog).getByText(/en una carpeta compartida/)).toBeInTheDocument()
    expect(within(dialog).queryByRole('link')).not.toBeInTheDocument()
  })

  it('desde el visor, un correo adjunto se abre en el lector', () => {
    render(<MessageReader message={root} file={file} />)
    fireEvent.click(screen.getByRole('button', { name: 'Ver Presupuesto.xlsx' }))
    fireEvent.click(screen.getByRole('button', { name: 'Adjunto anterior' }))
    const dialog = screen.getByRole('dialog', { name: 'Cotización de acero' })
    expect(within(dialog).getByText(/^Correo · 900 B · 1 de 3$/)).toBeInTheDocument()

    fireEvent.click(within(dialog).getByRole('button', { name: 'Abrir correo' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1, name: 'Cotización de acero' })).toBeInTheDocument()
  })

  it('un correo adjunto que no se pudo leer sólo se ofrece para descargar como .msg', async () => {
    const broken = mail('Reenvío', {
      attachments: [attachment('Correo dañado', { kind: 'message', message: null, warnings: ['ilegible'] })],
    })
    render(<MessageReader message={broken} file={file} />)
    fireEvent.click(screen.getByRole('button', { name: 'Ver Correo dañado' }))
    const dialog = screen.getByRole('dialog', { name: 'Correo dañado' })

    expect(within(dialog).queryByRole('button', { name: 'Abrir correo' })).not.toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Descargar .msg' }))
    await waitFor(() => expect(mocks.saveBlob).toHaveBeenCalled())
    expect(mocks.fetchAttachment).toHaveBeenCalledWith(file, 0, 'Correo dañado', {
      preview: false,
      messagePath: [],
    })
  })
})
