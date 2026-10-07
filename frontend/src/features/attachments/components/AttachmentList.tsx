import { useId, useState } from 'react'
import {
  Attach16Regular,
  ChevronDown16Regular,
  ChevronUp16Regular,
  ErrorCircle16Regular,
} from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import { formatBytes } from '../../../lib/formatters'
import type { Attachment } from '../../../lib/types'
import type { AttachmentFiles } from '../hooks/useAttachmentFiles'
import { FileChip, PreviewCard } from './AttachmentTiles'
import { DownloadAllButton } from './DownloadAllButton'
import type { Entry } from './AttachmentTiles'

type Props = {
  /** Lista completa del correo: el índice de cada adjunto es su posición aquí (la que usa la API). */
  attachments: Attachment[]
  /** Subconjunto a mostrar; por defecto todos. */
  indices?: number[]
  files: AttachmentFiles
  onOpen: (index: number) => void
  /** Plegar a partir de `COLLAPSED_COUNT`; la galería completa lo desactiva. */
  collapsible?: boolean
  heading?: string
}

/** Con más adjuntos que este número la lista se pliega para no empujar el cuerpo fuera de la vista. */
const COLLAPSED_COUNT = 6

export function AttachmentList({
  attachments,
  indices,
  files,
  onOpen,
  collapsible: canCollapse = true,
  heading,
}: Props) {
  const headingId = useId()
  const [downloading, setDownloading] = useState<ReadonlySet<number>>(new Set())
  const [failed, setFailed] = useState<number | null>(null)
  const [expanded, setExpanded] = useState(false)

  // Las vistas previas primero, como en un lector de correo; el índice original se conserva para la API.
  const shown = indices ?? attachments.map((_, index) => index)
  const entries: Entry[] = shown.map((index) => ({ attachment: attachments[index], index }))
  const ordered = [
    ...entries.filter((entry) => entry.attachment.preview),
    ...entries.filter((e) => !e.attachment.preview),
  ]
  const collapsible = canCollapse && ordered.length > COLLAPSED_COUNT
  const visible = collapsible && !expanded ? ordered.slice(0, COLLAPSED_COUNT) : ordered
  const previews = visible.filter((entry) => entry.attachment.preview)
  const others = visible.filter((entry) => !entry.attachment.preview)
  const knownSizes = entries
    .map((entry) => entry.attachment.size_bytes)
    .filter((size): size is number => size != null)
  const total = knownSizes.reduce((sum, size) => sum + size, 0)
  // Un ZIP vale la pena con dos o más archivos que traen bytes (un enlace no se descarga).
  const zippable = attachments.filter((attachment) => attachment.kind !== 'link').length >= 2

  async function download({ attachment, index }: Entry) {
    setDownloading((current) => new Set(current).add(index))
    setFailed(null)
    try {
      await files.download(attachment, index)
    } catch {
      setFailed(index)
    } finally {
      setDownloading((current) => {
        const next = new Set(current)
        next.delete(index)
        return next
      })
    }
  }

  const tileProps = (entry: Entry) => ({
    entry,
    busy: downloading.has(entry.index),
    onOpen: () => onOpen(entry.index),
    onDownload: () => void download(entry),
  })

  return (
    <section className="attachments" aria-labelledby={headingId}>
      <div className="attachments__head">
        <h2 id={headingId} className="attachments__title">
          <Attach16Regular aria-hidden="true" />
          {heading ?? `${entries.length} ${entries.length === 1 ? 'dato adjunto' : 'datos adjuntos'}`}
          {knownSizes.length > 0 && <span className="attachments__total"> ({formatBytes(total)})</span>}
        </h2>
        <div className="attachments__actions">
          {zippable && <DownloadAllButton onDownloadAll={files.downloadAll} />}
          {collapsible && (
            <Button
              variant="subtle"
              size="sm"
              aria-expanded={expanded}
              onClick={() => setExpanded((value) => !value)}
            >
              {expanded ? 'Mostrar menos' : `Mostrar los ${entries.length}`}
              {expanded ? (
                <ChevronUp16Regular aria-hidden="true" />
              ) : (
                <ChevronDown16Regular aria-hidden="true" />
              )}
            </Button>
          )}
        </div>
      </div>
      {previews.length > 0 && (
        <ul className="attachments__previews">
          {previews.map((entry) => (
            <li key={entry.index}>
              <PreviewCard {...tileProps(entry)} />
            </li>
          ))}
        </ul>
      )}
      {others.length > 0 && (
        <ul className="attachments__files">
          {others.map((entry) => (
            <li key={entry.index}>
              <FileChip {...tileProps(entry)} />
            </li>
          ))}
        </ul>
      )}
      {failed !== null && (
        <p className="attachments__error" role="alert">
          <ErrorCircle16Regular aria-hidden="true" />
          No se pudo descargar “{attachments[failed]?.name}”. Inténtalo otra vez.
        </p>
      )}
    </section>
  )
}
