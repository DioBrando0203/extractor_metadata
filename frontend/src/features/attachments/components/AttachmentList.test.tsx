import { useState } from 'react'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Attachment } from '../../../lib/types'

const mocks = vi.hoisted(() => ({ fetchAttachment: vi.fn(), saveBlob: vi.fn() }))
vi.mock('../../../lib/api', () => mocks)
import { useAttachmentFiles } from '../hooks/useAttachmentFiles'
import { AttachmentList } from './AttachmentList'
import { AttachmentViewer } from './AttachmentViewer'

const PIXEL = 'data:image/png;base64,iVBORw0KGgo='
const file = new File(['msg'], 'correo.msg')
const attachment = (name: string, extra: Partial<Attachment> = {}): Attachment => ({
  name,
  size_bytes: 2048,
  metadata: [],
  warnings: [],
  ...extra,
})

/** Compone lista y visor igual que `MessageViewer`, que es quien decide qué adjunto se ve. */
function Harness({ attachments }: { attachments: Attachment[] }) {
  const files = useAttachmentFiles(file)
  const [viewing, setViewing] = useState<number | null>(null)
  return (
    <>
      <AttachmentList attachments={attachments} files={files} onOpen={setViewing} />
      {viewing !== null && (
        <AttachmentViewer
          attachments={attachments}
          index={viewing}
          files={files}
          onNavigate={setViewing}
          onClose={() => setViewing(null)}
        />
      )}
    </>
  )
}

describe('AttachmentList', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:vista'), revokeObjectURL: vi.fn() })
    mocks.fetchAttachment.mockResolvedValue({
      blob: new Blob(['x'], { type: 'image/png' }),
      filename: 'foto.png',
    })
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it('muestra la miniatura de las imágenes y un chip para los demás archivos', () => {
    render(
      <Harness
        attachments={[
          attachment('plano.dwg'),
          attachment('foto.png', { preview: PIXEL, preview_source: 'image' }),
        ]}
      />,
    )
    const card = screen.getByRole('button', { name: 'Ver foto.png' })
    expect(card.querySelector('img')).toHaveAttribute('src', PIXEL)
    expect(screen.getByRole('button', { name: 'Ver plano.dwg' }).querySelector('img')).toBeNull()
    expect(screen.getByRole('button', { name: 'Descargar plano.dwg' })).toBeInTheDocument()
  })

  it('abre el visor con la imagen, navega al siguiente adjunto y se cierra devolviendo el foco', async () => {
    render(
      <Harness
        attachments={[
          attachment('foto.png', { preview: PIXEL, preview_source: 'image' }),
          attachment('plano.dwg', { preview: PIXEL, preview_source: 'embedded' }),
        ]}
      />,
    )
    const opener = screen.getByRole('button', { name: 'Ver foto.png' })
    opener.focus()
    fireEvent.click(opener)
    const dialog = await screen.findByRole('dialog', { name: 'foto.png' })
    expect(await within(dialog).findByRole('img', { name: 'foto.png' })).toHaveAttribute('src', 'blob:vista')
    expect(mocks.fetchAttachment).toHaveBeenCalledWith(file, 0, 'foto.png', { preview: false })

    fireEvent.click(within(dialog).getByRole('button', { name: 'Adjunto siguiente' }))
    expect(screen.getByRole('dialog', { name: 'plano.dwg' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Miniatura de plano.dwg' })).toHaveAttribute('src', PIXEL)

    fireEvent.click(screen.getByRole('button', { name: 'Cerrar vista previa' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(opener).toHaveFocus()
  })

  it('sin vista previa ofrece descargar y muestra los detalles del archivo', async () => {
    render(
      <Harness
        attachments={[
          attachment('plano.dwg', {
            metadata: [{ group: 'AutoCAD', label: 'Versión de formato', value: 'DWG 2018 (formato)' }],
          }),
        ]}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Ver plano.dwg' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('No hay vista previa para este tipo de archivo.')).toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: /Detalles/ }))
    expect(within(dialog).getByText('DWG 2018 (formato)')).toBeInTheDocument()
    fireEvent.click(within(dialog).getAllByRole('button', { name: /Descargar/ })[0])
    await waitFor(() => expect(mocks.saveBlob).toHaveBeenCalledOnce())
  })
})
