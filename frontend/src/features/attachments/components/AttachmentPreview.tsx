import { useEffect, useState } from 'react'
import { ArrowDownload20Regular } from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import { Spinner } from '../../../components/ui/Spinner'
import type { Attachment } from '../../../lib/types'
import type { useAttachmentFiles } from '../hooks/useAttachmentFiles'
import { decodeText } from '../lib/decodeText'
import { fileKind } from '../lib/fileKind'
import { blobTypeFor, needsFile, TEXT_PREVIEW_LIMIT } from '../lib/viewerMode'
import type { ViewerMode } from '../lib/viewerMode'
import { FileTypeIcon } from './FileTypeIcon'

type Props = {
  attachment: Attachment
  index: number
  mode: ViewerMode
  files: ReturnType<typeof useAttachmentFiles>
  onDownload: () => void
}

type Loaded =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'ready'; url?: string; text?: string; cut?: boolean }

/**
 * Contenido del visor. Se monta con `key` por adjunto, así el estado inicial siempre es "cargando".
 * Todo contenido se muestra como dato (img, iframe de PDF, pre, video): nunca HTML del adjunto.
 */
export function AttachmentPreview({ attachment, index, mode, files, onDownload }: Props) {
  const [loaded, setLoaded] = useState<Loaded>({ status: 'loading' })

  useEffect(() => {
    if (!needsFile(mode)) return
    let active = true
    const request =
      mode === 'text'
        ? files.load(attachment, index).then(async ({ blob }) => ({
            text: decodeText(await blob.slice(0, TEXT_PREVIEW_LIMIT).arrayBuffer()),
            cut: blob.size > TEXT_PREVIEW_LIMIT,
          }))
        : files
            .objectUrl(
              attachment,
              index,
              mode === 'converted' ? 'preview' : 'original',
              blobTypeFor(mode, attachment.name),
            )
            .then((url) => ({ url }))
    request
      .then((result) => active && setLoaded({ status: 'ready', ...result }))
      .catch(() => active && setLoaded({ status: 'error' }))
    return () => {
      active = false
    }
  }, [attachment, index, mode, files])

  if (mode === 'embedded') {
    return (
      <figure className="viewer-embedded">
        <img src={attachment.preview ?? undefined} alt={`Miniatura de ${attachment.name}`} />
        <figcaption>
          Miniatura guardada dentro del archivo por el programa que lo creó. Puede no reflejar la última
          versión; para ver el contenido completo, descárgalo y ábrelo con su aplicación.
        </figcaption>
      </figure>
    )
  }
  if (mode === 'none') {
    return (
      <NoPreview
        attachment={attachment}
        message="No hay vista previa para este tipo de archivo."
        onDownload={onDownload}
      />
    )
  }
  if (loaded.status === 'loading') return <Spinner size="lg" tone="inverted" label="Cargando vista previa" />
  if (loaded.status === 'error') {
    return (
      <NoPreview
        attachment={attachment}
        message="No se pudo mostrar la vista previa."
        onDownload={onDownload}
      />
    )
  }
  if (mode === 'pdf')
    return <iframe className="viewer-pdf" src={loaded.url} title={`Vista previa de ${attachment.name}`} />
  if (mode === 'video') return <video className="viewer-media" src={loaded.url} controls />
  if (mode === 'audio') {
    return (
      <div className="viewer-sheet viewer-sheet--audio">
        <FileTypeIcon kind="media" size="lg" />
        <audio src={loaded.url} controls />
      </div>
    )
  }
  if (mode === 'text') {
    return (
      <div className="viewer-sheet">
        <pre className="viewer-text">{loaded.text}</pre>
        {loaded.cut && (
          <p className="viewer-note">
            Se muestra el primer megabyte. Descarga el archivo para verlo completo.
          </p>
        )}
      </div>
    )
  }
  return <img className="viewer-image" src={loaded.url} alt={attachment.name} />
}

function NoPreview({
  attachment,
  message,
  onDownload,
}: {
  attachment: Attachment
  message: string
  onDownload: () => void
}) {
  return (
    <div className="viewer-sheet viewer-sheet--empty">
      <FileTypeIcon kind={fileKind(attachment.name, attachment.content_type)} size="lg" />
      <p className="viewer-sheet__name">{attachment.name}</p>
      <p className="viewer-sheet__message">{message}</p>
      <Button onClick={onDownload}>
        <ArrowDownload20Regular aria-hidden="true" /> Descargar
      </Button>
    </div>
  )
}
