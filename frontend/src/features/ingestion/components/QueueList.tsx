import {
  CircleAlert,
  Clock,
  LoaderCircle,
  Paperclip,
  Plus,
  RotateCcw,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import { Avatar } from '../../../components/ui/Avatar'
import { Button } from '../../../components/ui/Button'
import { formatBytes, formatListDate } from '../../../lib/formatters'
import { fileStem, messageTitle, parseAddress, previewLine } from '../../../lib/mail'
import type { Message, QueueItem } from '../../../lib/types'
import { fileValidationError } from '../lib/validation'

type Props = {
  items: QueueItem[]
  selectedId: string | null
  onSelect: (id: string) => void
  onRetry: (id: string) => void
  onClear: () => void
  onAdd: () => void
}

export function QueueList({ items, selectedId, onSelect, onRetry, onClear, onAdd }: Props) {
  return (
    <aside className="mail-list" aria-label="Bandeja de correos">
      <div className="mail-list__header">
        <Button className="mail-list__add" onClick={onAdd}>
          <Plus size={16} aria-hidden="true" /> Abrir MSG
        </Button>
        <div className="mail-list__title">
          <h2>Bandeja</h2>
          <span className="count">{items.length}</span>
          <Button variant="ghost" size="sm" className="mail-list__clear" onClick={onClear}>
            <Trash2 size={14} aria-hidden="true" /> Limpiar
          </Button>
        </div>
      </div>
      <ul className="mail-list__items">
        {items.map((item) => (
          <QueueRow
            key={item.id}
            item={item}
            selected={item.id === selectedId}
            onSelect={() => onSelect(item.id)}
            onRetry={() => onRetry(item.id)}
          />
        ))}
      </ul>
      <p className="mail-list__note">
        <ShieldCheck size={14} aria-hidden="true" /> Los archivos sólo viven en la memoria de esta sesión.
      </p>
    </aside>
  )
}

type RowProps = { item: QueueItem; selected: boolean; onSelect: () => void; onRetry: () => void }

function QueueRow({ item, selected, onSelect, onRetry }: RowProps) {
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
          variant="ghost"
          size="sm"
          iconOnly
          className="mail-item__retry"
          aria-label={`Reintentar ${item.file.name}`}
          title="Reintentar"
          onClick={onRetry}
        >
          <RotateCcw size={14} aria-hidden="true" />
        </Button>
      )}
    </li>
  )
}

/** Fila de un correo ya leído: remitente, fecha, asunto y primera línea, como en un lector de correo. */
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
          {date && <span className="mail-item__date">{date}</span>}
        </span>
        <span className="mail-item__line">
          <span className="mail-item__subject">{messageTitle(message.subject, fileName).text}</span>
          {message.attachments.length > 0 && (
            <span className="mail-item__clip" title={`${message.attachments.length} adjuntos`}>
              <Paperclip size={13} aria-hidden="true" />
              <span className="sr-only">, con adjuntos</span>
            </span>
          )}
        </span>
        <span className="mail-item__line">
          {message.status === 'partial' && <span className="chip chip--warn">Parcial</span>}
          <span className="mail-item__preview">{preview || 'Sin texto legible'}</span>
        </span>
      </span>
    </>
  )
}

const PENDING = {
  queued: { icon: <Clock size={16} />, text: 'En espera' },
  extracting: { icon: <LoaderCircle size={16} className="spin" />, text: 'Leyendo correo…' },
  error: { icon: <CircleAlert size={16} />, text: 'No se pudo leer' },
} as const

/** Fila de un archivo en cola, en lectura o con error: todavía no hay datos del correo. */
function PendingSummary({ item }: { item: QueueItem }) {
  const state = PENDING[item.status as keyof typeof PENDING] ?? PENDING.queued
  return (
    <>
      <span className={`status-dot status-dot--${item.status}`} aria-hidden="true">
        {state.icon}
      </span>
      <span className="mail-item__content">
        <span className="mail-item__line">
          <span className="mail-item__from">{fileStem(item.file.name)}</span>
        </span>
        <span className="mail-item__line">
          <span className="mail-item__subject mail-item__status">{state.text}</span>
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
