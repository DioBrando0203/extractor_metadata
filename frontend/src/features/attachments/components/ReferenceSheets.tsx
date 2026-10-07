import { ArrowDownload20Regular, MailRead20Regular, Open20Regular } from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import type { Attachment } from '../../../lib/types'
import { describeAttachment } from '../lib/fileKind'
import { isWebLink } from '../lib/link'
import { FileTypeIcon } from './FileTypeIcon'

/**
 * Adjunto que vive en la nube o en una carpeta compartida: no hay bytes en el correo. Una dirección web
 * se abre en otra pestaña sin enviar de dónde viene; una ruta de red sólo se muestra para copiarla.
 */
export function LinkSheet({ attachment }: { attachment: Attachment }) {
  const { link } = attachment
  const web = isWebLink(link)
  return (
    <div className="viewer-sheet viewer-sheet--empty">
      <FileTypeIcon kind={describeAttachment(attachment).kind} size="lg" />
      <p className="viewer-sheet__name">{attachment.name}</p>
      <p className="viewer-sheet__message">
        Este archivo no viaja dentro del correo: está {web ? 'en la nube' : 'en una carpeta compartida'}. Para
        verlo necesitas acceso con tu cuenta o desde la red de tu organización.
      </p>
      {link ? (
        <p className="viewer-sheet__address">{link}</p>
      ) : (
        <p className="viewer-sheet__message">No se pudo leer su dirección.</p>
      )}
      {web && (
        <a
          className="button button--primary button--md"
          href={link}
          target="_blank"
          rel="noopener noreferrer"
        >
          <Open20Regular aria-hidden="true" /> Abrir enlace
        </a>
      )}
    </div>
  )
}

type MessageSheetProps = { attachment: Attachment; onOpen?: () => void; onDownload: () => void }

/** Correo adjunto dentro del visor: se abre como un correo propio o se descarga como `.msg`. */
export function MessageSheet({ attachment, onOpen, onDownload }: MessageSheetProps) {
  const readable = Boolean(attachment.message && onOpen)
  return (
    <div className="viewer-sheet viewer-sheet--empty">
      <FileTypeIcon kind="mail" size="lg" />
      <p className="viewer-sheet__name">{attachment.name}</p>
      <p className="viewer-sheet__message">
        {readable
          ? 'Correo adjunto. Ábrelo para leerlo como cualquier otro correo.'
          : 'No se pudo abrir este correo adjunto aquí. Descárgalo para abrirlo aparte.'}
      </p>
      <div className="viewer-sheet__actions">
        {readable && (
          <Button onClick={onOpen}>
            <MailRead20Regular aria-hidden="true" /> Abrir correo
          </Button>
        )}
        <Button variant={readable ? 'secondary' : 'primary'} onClick={onDownload}>
          <ArrowDownload20Regular aria-hidden="true" /> Descargar .msg
        </Button>
      </div>
    </div>
  )
}
