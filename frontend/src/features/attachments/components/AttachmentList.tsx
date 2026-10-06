import { useId, useState } from 'react'
import {
  ChevronDown,
  ChevronUp,
  CircleAlert,
  Download,
  DraftingCompass,
  File,
  FileArchive,
  FileCode,
  FileImage,
  FileSpreadsheet,
  FileText,
  FileVideo,
  LoaderCircle,
  Mail,
  Paperclip,
  Presentation,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import { downloadAttachment } from '../../../lib/api'
import { formatBytes } from '../../../lib/formatters'
import type { Attachment } from '../../../lib/types'
import { fileKind, kindLabel } from '../lib/fileKind'
import type { FileKind } from '../lib/fileKind'

type Props = { attachments: Attachment[]; file: File }

/** Con más adjuntos que este número, la lista se pliega para no empujar el cuerpo fuera de la vista. */
const COLLAPSED_COUNT = 6

const ICONS: Record<FileKind, LucideIcon> = {
  pdf: FileText,
  word: FileText,
  excel: FileSpreadsheet,
  slides: Presentation,
  image: FileImage,
  cad: DraftingCompass,
  archive: FileArchive,
  mail: Mail,
  text: FileCode,
  media: FileVideo,
  other: File,
}

export function AttachmentList({ attachments, file }: Props) {
  const headingId = useId()
  const [downloading, setDownloading] = useState<ReadonlySet<number>>(new Set())
  const [failed, setFailed] = useState<number | null>(null)
  const [expanded, setExpanded] = useState(false)

  const collapsible = attachments.length > COLLAPSED_COUNT
  const visible = collapsible && !expanded ? attachments.slice(0, COLLAPSED_COUNT) : attachments
  const knownSizes = attachments.map((item) => item.size_bytes).filter((size): size is number => size != null)
  const total = knownSizes.reduce((sum, size) => sum + size, 0)

  async function download(attachment: Attachment, index: number) {
    setDownloading((current) => new Set(current).add(index))
    setFailed(null)
    try {
      // El índice es la posición en la lista completa que devolvió el backend, no en la lista visible.
      await downloadAttachment(file, index, attachment.name)
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

  return (
    <section className="attachments" aria-labelledby={headingId}>
      <div className="attachments__head">
        <h2 id={headingId} className="attachments__title">
          <Paperclip size={15} aria-hidden="true" />
          {attachments.length} {attachments.length === 1 ? 'adjunto' : 'adjuntos'}
          {knownSizes.length > 0 && <span className="attachments__total"> ({formatBytes(total)})</span>}
        </h2>
        {collapsible && (
          <Button
            variant="ghost"
            size="sm"
            aria-expanded={expanded}
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? 'Mostrar menos' : `Mostrar los ${attachments.length}`}
            {expanded ? (
              <ChevronUp size={14} aria-hidden="true" />
            ) : (
              <ChevronDown size={14} aria-hidden="true" />
            )}
          </Button>
        )}
      </div>
      <ul className="attachments__grid">
        {visible.map((attachment, index) => {
          const kind = fileKind(attachment.name, attachment.content_type)
          const Icon = ICONS[kind]
          const busy = downloading.has(index)
          return (
            <li key={`${attachment.name}-${index}`}>
              <button
                type="button"
                className="attachment-tile"
                data-kind={kind}
                aria-label={`Descargar ${attachment.name}`}
                aria-busy={busy || undefined}
                disabled={busy}
                title={attachment.name}
                onClick={() => void download(attachment, index)}
              >
                <span className="attachment-tile__icon" aria-hidden="true">
                  <Icon size={20} />
                </span>
                <span className="attachment-tile__text">
                  <span className="attachment-tile__name">{attachment.name}</span>
                  <span className="attachment-tile__meta">
                    {busy
                      ? 'Preparando descarga…'
                      : `${kindLabel(attachment.name, attachment.content_type)} · ${formatBytes(attachment.size_bytes)}`}
                  </span>
                </span>
                <span className="attachment-tile__action" aria-hidden="true">
                  {busy ? <LoaderCircle size={16} className="spin" /> : <Download size={16} />}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
      {failed !== null && (
        <p className="attachments__error" role="alert">
          <CircleAlert size={15} aria-hidden="true" />
          No se pudo descargar “{attachments[failed]?.name}”. Inténtalo otra vez.
        </p>
      )}
    </section>
  )
}
