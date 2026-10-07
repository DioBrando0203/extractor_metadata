import { useEffect, useId, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import {
  ArrowDownload20Regular,
  ChevronLeft24Regular,
  ChevronRight24Regular,
  Dismiss20Regular,
  Info20Regular,
} from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import { Spinner } from '../../../components/ui/Spinner'
import type { Attachment } from '../../../lib/types'
import type { useAttachmentFiles } from '../hooks/useAttachmentFiles'
import { attachmentMeta, describeAttachment } from '../lib/fileKind'
import { viewerMode } from '../lib/viewerMode'
import { AttachmentDetails } from './AttachmentDetails'
import { AttachmentPreview } from './AttachmentPreview'
import { FileTypeIcon } from './FileTypeIcon'

type Props = {
  attachments: Attachment[]
  index: number
  files: ReturnType<typeof useAttachmentFiles>
  onNavigate: (index: number) => void
  onClose: () => void
  /** Abre un correo adjunto como correo propio (navegación del lector). */
  onOpenMessage?: (index: number) => void
}

/** Visor a pantalla completa: ver un adjunto de frente, pasar al siguiente y descargarlo. */
export function AttachmentViewer({ attachments, index, files, onNavigate, onClose, onOpenMessage }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)
  const titleId = useId()
  const [details, setDetails] = useState(false)
  const [download, setDownload] = useState<'idle' | 'busy' | 'error'>('idle')
  const attachment = attachments[index]
  const count = attachments.length
  const mode = viewerMode(attachment)

  useEffect(() => {
    const node = dialog.current
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    // showModal deja el resto de la página inerte y atrapa el foco; jsdom puede no implementarlo.
    if (node && !node.open) {
      if (typeof node.showModal === 'function') node.showModal()
      else node.setAttribute('open', '')
    }
    return () => {
      if (node?.open && typeof node.close === 'function') node.close()
      opener?.focus()
    }
  }, [])

  const go = (step: number) => {
    setDownload('idle')
    onNavigate((index + step + count) % count)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLDialogElement>) => {
    if (count < 2 || event.target instanceof HTMLMediaElement) return
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault()
      go(event.key === 'ArrowLeft' ? -1 : 1)
    }
  }

  const save = async () => {
    setDownload('busy')
    try {
      await files.download(attachment, index)
      setDownload('idle')
    } catch {
      setDownload('error')
    }
  }

  return (
    <dialog
      ref={dialog}
      className="viewer"
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      onKeyDown={onKeyDown}
    >
      <header className="viewer__bar">
        <FileTypeIcon kind={describeAttachment(attachment).kind} size="sm" />
        <div className="viewer__title">
          <h2 id={titleId}>{attachment.name}</h2>
          <p>
            {attachmentMeta(attachment)}
            {count > 1 && ` · ${index + 1} de ${count}`}
          </p>
        </div>
        <div className="viewer__actions">
          <Button variant="subtle" aria-pressed={details} onClick={() => setDetails((value) => !value)}>
            <Info20Regular aria-hidden="true" /> <span className="viewer__label">Detalles</span>
          </Button>
          {attachment.kind !== 'link' && (
            <Button variant="subtle" onClick={() => void save()} disabled={download === 'busy'}>
              {download === 'busy' ? (
                <Spinner size="sm" tone="inverted" />
              ) : (
                <ArrowDownload20Regular aria-hidden="true" />
              )}
              <span className="viewer__label">Descargar</span>
            </Button>
          )}
          <Button
            variant="subtle"
            iconOnly
            aria-label="Cerrar vista previa"
            title="Cerrar (Esc)"
            onClick={onClose}
          >
            <Dismiss20Regular aria-hidden="true" />
          </Button>
        </div>
      </header>
      {download === 'error' && (
        <p className="viewer__alert" role="alert">
          No se pudo descargar el archivo. Inténtalo otra vez.
        </p>
      )}
      <div className="viewer__body">
        <div className="viewer__stage">
          <AttachmentPreview
            key={index}
            attachment={attachment}
            index={index}
            mode={mode}
            files={files}
            onDownload={() => void save()}
            onOpenMessage={onOpenMessage && (() => onOpenMessage(index))}
          />
          {count > 1 && (
            <>
              <button
                type="button"
                className="viewer__nav viewer__nav--prev"
                aria-label="Adjunto anterior"
                onClick={() => go(-1)}
              >
                <ChevronLeft24Regular aria-hidden="true" />
              </button>
              <button
                type="button"
                className="viewer__nav viewer__nav--next"
                aria-label="Adjunto siguiente"
                onClick={() => go(1)}
              >
                <ChevronRight24Regular aria-hidden="true" />
              </button>
            </>
          )}
        </div>
        {details && <AttachmentDetails attachment={attachment} />}
      </div>
    </dialog>
  )
}
