import {
  ArrowClockwise16Regular,
  Attach12Regular,
  Clock16Regular,
  ErrorCircle16Filled,
} from '@fluentui/react-icons'
import { Avatar } from '../../../components/ui/Avatar'
import { Button } from '../../../components/ui/Button'
import { Spinner } from '../../../components/ui/Spinner'
import { formatBytes, formatListDate } from '../../../lib/formatters'
import { fileStem, messageTitle, parseAddress, previewLine } from '../../../lib/mail'
import type { Message, QueueItem } from '../../../lib/types'
import { fileValidationError } from '../lib/validation'

type Props = { item: QueueItem; selected: boolean; onSelect: () => void; onRetry: () => void }

export function QueueRow({ item, selected, onSelect, onRetry }: Props) {
  const retryable = item.status === 'error' && !fileValidationError(item.file)
  const classes = [
    'mail-item',
    `mail-item--${item.status}`,
    selected && 'is-selected',
    retryable && 'has-action',
  ]
  return (
    <li className="mail-list__row">
      <button
        type="button"
        className={classes.filter(Boolean).join(' ')}
        aria-current={selected ? 'true' : undefined}
        onClick={onSelect}
      >
        {item.message ? (
          <MessageSummary message={item.message} fileName={item.file.name} />
        ) : (
          <PendingSummary item={item} />
        )}
      </button>
      {retryable && (
        <Button
          variant="subtle"
          size="sm"
          iconOnly
          className="mail-item__retry"
          aria-label={`Reintentar ${item.file.name}`}
          title="Reintentar"
          onClick={onRetry}
        >
          <ArrowClockwise16Regular aria-hidden="true" />
        </Button>
      )}
    </li>
  )
}

/** Correo leído: remitente, asunto con fecha y primera línea, como en la lista de un cliente de correo. */
function MessageSummary({ message, fileName }: { message: Message; fileName: string }) {
  const sender = message.sender ? parseAddress(message.sender) : null
  const date = formatListDate(message.sent_at ?? message.received_at)
  const preview = previewLine(message.body_preview)
  return (
    <>
      <Avatar name={sender?.name} size="sm" />
      <span className="mail-item__content">
        <span className="mail-item__line">
          <span className={`mail-item__from ${sender ? '' : 'is-missing'}`}>
            {sender?.name ?? 'Remitente desconocido'}
          </span>
          {message.attachments.length > 0 && (
            <span className="mail-item__clip" title={`${message.attachments.length} datos adjuntos`}>
              <Attach12Regular aria-hidden="true" />
              <span className="sr-only">, con datos adjuntos</span>
            </span>
          )}
        </span>
        <span className="mail-item__line">
          <span className="mail-item__subject">{messageTitle(message.subject, fileName).text}</span>
          {date && <span className="mail-item__date">{date}</span>}
        </span>
        <span className="mail-item__line">
          {message.status === 'partial' && <span className="chip chip--warn">Parcial</span>}
          <span className="mail-item__preview">{preview || 'Sin texto legible'}</span>
        </span>
      </span>
    </>
  )
}

/** Archivo en cola, en lectura o con error: todavía no hay datos del correo. */
function PendingSummary({ item }: { item: QueueItem }) {
  const icon =
    item.status === 'extracting' ? (
      <Spinner size="sm" />
    ) : item.status === 'error' ? (
      <ErrorCircle16Filled aria-hidden="true" />
    ) : (
      <Clock16Regular aria-hidden="true" />
    )
  const status =
    item.status === 'extracting'
      ? 'Leyendo correo…'
      : item.status === 'error'
        ? 'No se pudo leer'
        : 'En espera'
  return (
    <>
      <span className={`status-dot status-dot--${item.status}`}>{icon}</span>
      <span className="mail-item__content">
        <span className="mail-item__line">
          <span className="mail-item__from">{fileStem(item.file.name)}</span>
        </span>
        <span className="mail-item__line">
          <span className="mail-item__subject mail-item__status">{status}</span>
        </span>
        <span className="mail-item__line">
          <span className="mail-item__preview">
            {item.status === 'error' && item.error ? item.error : formatBytes(item.file.size)}
          </span>
        </span>
      </span>
    </>
  )
}
