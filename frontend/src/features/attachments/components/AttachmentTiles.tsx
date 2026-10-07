import { ArrowDownload20Regular } from '@fluentui/react-icons'
import { Spinner } from '../../../components/ui/Spinner'
import type { Attachment } from '../../../lib/types'
import { attachmentMeta, describeAttachment } from '../lib/fileKind'
import { FileTypeIcon } from './FileTypeIcon'

/** Adjunto con su posición en la lista original del backend (la que usa la API). */
export type Entry = { attachment: Attachment; index: number }

type TileProps = { entry: Entry; busy: boolean; onOpen: () => void; onDownload: () => void }

function DownloadButton({ attachment, busy, onDownload }: Omit<TileProps, 'entry' | 'onOpen'> & Entry) {
  // Un enlace no trae bytes dentro del correo: no hay nada que descargar.
  if (attachment.kind === 'link') return null
  return (
    <button
      type="button"
      className="attachment-download"
      aria-label={`Descargar ${attachment.name}`}
      title="Descargar"
      disabled={busy}
      aria-busy={busy || undefined}
      onClick={onDownload}
    >
      {busy ? <Spinner size="sm" /> : <ArrowDownload20Regular aria-hidden="true" />}
    </button>
  )
}

/** Adjunto con miniatura: la imagen se ve de frente y al pulsarla se abre el visor. */
export function PreviewCard({ entry, busy, onOpen, onDownload }: TileProps) {
  const { attachment } = entry
  return (
    <div className="attachment-card" data-source={attachment.preview_source ?? undefined}>
      <button
        type="button"
        className="attachment-card__open"
        aria-label={`Ver ${attachment.name}`}
        onClick={onOpen}
      >
        <span className="attachment-card__thumb">
          <img src={attachment.preview ?? undefined} alt="" loading="lazy" decoding="async" />
        </span>
        <span className="attachment-card__info">
          <FileTypeIcon kind={describeAttachment(attachment).kind} size="sm" />
          <span className="attachment-card__text">
            <span className="attachment-card__name" title={attachment.name}>
              {attachment.name}
            </span>
            <span className="attachment-card__meta">{attachmentMeta(attachment)}</span>
          </span>
        </span>
      </button>
      <DownloadButton {...entry} busy={busy} onDownload={onDownload} />
    </div>
  )
}

/** Adjunto sin miniatura: chip compacto con icono de tipo, como en la bandeja de un cliente de correo. */
export function FileChip({ entry, busy, onOpen, onDownload }: TileProps) {
  const { attachment } = entry
  const action = attachment.kind === 'message' && attachment.message ? 'Abrir' : 'Ver'
  return (
    <div className="attachment-chip" data-kind={attachment.kind ?? 'file'}>
      <button
        type="button"
        className="attachment-chip__open"
        aria-label={`${action} ${attachment.name}`}
        onClick={onOpen}
      >
        <FileTypeIcon kind={describeAttachment(attachment).kind} />
        <span className="attachment-chip__text">
          <span className="attachment-chip__name" title={attachment.name}>
            {attachment.name}
          </span>
          <span className="attachment-chip__meta">
            {busy ? 'Preparando descarga…' : attachmentMeta(attachment)}
          </span>
        </span>
      </button>
      <DownloadButton {...entry} busy={busy} onDownload={onDownload} />
    </div>
  )
}
