import { CircleAlert, FileClock, FileText, LoaderCircle, RotateCcw } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import type { QueueItem } from '../../../lib/types'
import { fileValidationError } from '../lib/validation'

type Props = {
  items: QueueItem[]
  selectedId: string | null
  onSelect: (id: string) => void
  onRetry: (id: string) => void
  onClear: () => void
}
const labels = {
  queued: 'En cola',
  extracting: 'Extrayendo',
  complete: 'Completo',
  partial: 'Parcial',
  error: 'Error',
}
export function QueueList({ items, selectedId, onSelect, onRetry, onClear }: Props) {
  return (
    <aside className="message-list" aria-label="Bandeja de análisis">
      <div className="section-heading">
        <span>Bandeja de análisis</span>
        <span className="count">{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="empty-list">Los mensajes analizados aparecerán aquí durante esta sesión.</p>
      ) : (
        <>
          <ul className="queue-list">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  className={`message-card ${item.id === selectedId ? 'selected' : ''}`}
                  onClick={() => onSelect(item.id)}
                >
                  <span className="queue-card__icon">
                    {item.status === 'extracting' ? (
                      <LoaderCircle className="spin" size={16} />
                    ) : item.status === 'error' ? (
                      <CircleAlert size={16} />
                    ) : item.status === 'queued' ? (
                      <FileClock size={16} />
                    ) : (
                      <FileText size={16} />
                    )}
                  </span>
                  <span className="queue-card__text">
                    <strong>{item.message?.subject || item.file.name}</strong>
                    <small>
                      {labels[item.status]} · {Math.ceil(item.file.size / 1024)} KB
                    </small>
                  </span>
                </button>
                {item.status === 'error' && !fileValidationError(item.file) && (
                  <Button
                    variant="ghost"
                    className="retry-button"
                    aria-label={`Reintentar ${item.file.name}`}
                    onClick={() => onRetry(item.id)}
                  >
                    <RotateCcw size={14} />
                  </Button>
                )}
              </li>
            ))}
          </ul>
          <Button variant="ghost" className="clear-session" onClick={onClear}>
            Limpiar sesión
          </Button>
        </>
      )}
    </aside>
  )
}
