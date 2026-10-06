import { ShieldCheckmark16Regular } from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import type { QueueItem } from '../../../lib/types'
import { QueueRow } from './QueueRow'

type Props = {
  items: QueueItem[]
  total: number
  query: string
  selectedId: string | null
  onSelect: (id: string) => void
  onRetry: (id: string) => void
  onClearQuery: () => void
}

/** Lista de correos de la sesión, con el aspecto de la lista de mensajes de un cliente de correo. */
export function QueueList({ items, total, query, selectedId, onSelect, onRetry, onClearQuery }: Props) {
  const filtering = query.trim().length > 0
  return (
    <aside className="mail-list" aria-label="Bandeja de correos">
      <div className="mail-list__header">
        <h2>Bandeja</h2>
        <span className="count">{filtering ? `${items.length} de ${total}` : total}</span>
      </div>
      {items.length > 0 ? (
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
      ) : (
        <div className="mail-list__empty">
          <p>No hay correos que coincidan con “{query.trim()}”.</p>
          <Button variant="secondary" size="sm" onClick={onClearQuery}>
            Borrar búsqueda
          </Button>
        </div>
      )}
      <p className="mail-list__note">
        <ShieldCheckmark16Regular aria-hidden="true" /> Los archivos sólo viven en la memoria de esta sesión.
      </p>
    </aside>
  )
}
