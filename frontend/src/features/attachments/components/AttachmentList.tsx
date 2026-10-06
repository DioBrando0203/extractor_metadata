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
import { useAttachmentFiles } from '../hooks/useAttachmentFiles'
import { FileChip, PreviewCard } from './AttachmentTiles'
import type { Entry } from './AttachmentTiles'
import { AttachmentViewer } from './AttachmentViewer'

type Props = { attachments: Attachment[]; file: File }

/** Con más adjuntos que este número la lista se pliega para no empujar el cuerpo fuera de la vista. */
const COLLAPSED_COUNT = 6

export function AttachmentList({ attachments, file }: Props) {
  const headingId = useId()
  const files = useAttachmentFiles(file)
  const [downloading, setDownloading] = useState<ReadonlySet<number>>(new Set())
  const [failed, setFailed] = useState<number | null>(null)
  const [expanded, setExpanded] = useState(false)
  const [viewing, setViewing] = useState<number | null>(null)

  // Las vistas previas primero, como en un lector de correo; el índice original se conserva para la API.
  const entries: Entry[] = attachments.map((attachment, index) => ({ attachment, index }))
  const ordered = [
    ...entries.filter((entry) => entry.attachment.preview),
    ...entries.filter((e) => !e.attachment.preview),
  ]
  const collapsible = ordered.length > COLLAPSED_COUNT
  const visible = collapsible && !expanded ? ordered.slice(0, COLLAPSED_COUNT) : ordered
  const previews = visible.filter((entry) => entry.attachment.preview)
  const others = visible.filter((entry) => !entry.attachment.preview)
  const knownSizes = attachments.map((item) => item.size_bytes).filter((size): size is number => size != null)
  const total = knownSizes.reduce((sum, size) => sum + size, 0)

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
    onOpen: () => setViewing(entry.index),
    onDownload: () => void download(entry),
  })

  return (
    <section className="attachments" aria-labelledby={headingId}>
      <div className="attachments__head">
        <h2 id={headingId} className="attachments__title">
          <Attach16Regular aria-hidden="true" />
          {attachments.length} {attachments.length === 1 ? 'dato adjunto' : 'datos adjuntos'}
          {knownSizes.length > 0 && <span className="attachments__total"> ({formatBytes(total)})</span>}
        </h2>
        {collapsible && (
          <Button
            variant="subtle"
            size="sm"
            aria-expanded={expanded}
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? 'Mostrar menos' : `Mostrar los ${attachments.length}`}
            {expanded ? (
              <ChevronUp16Regular aria-hidden="true" />
            ) : (
              <ChevronDown16Regular aria-hidden="true" />
            )}
          </Button>
        )}
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
      {viewing !== null && (
        <AttachmentViewer
          attachments={attachments}
          index={viewing}
          files={files}
          onNavigate={setViewing}
          onClose={() => setViewing(null)}
        />
      )}
    </section>
  )
}
