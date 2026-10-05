import type { MetadataItem } from '../../lib/types'

type Props = { items: MetadataItem[]; emptyMessage?: string; ariaLabel: string }
export function MetadataTable({ items, emptyMessage = 'No hay campos disponibles.', ariaLabel }: Props) {
  if (!items.length) return <p className="empty-content">{emptyMessage}</p>
  return (
    <div className="metadata-table" role="table" aria-label={ariaLabel}>
      {items.map((item, index) => (
        <div className="metadata-table__row" role="row" key={`${item.group}-${item.label}-${index}`}>
          <span role="cell">{item.label}</span>
          <strong role="cell">{item.value}</strong>
        </div>
      ))}
    </div>
  )
}
