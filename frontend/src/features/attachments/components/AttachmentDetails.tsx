import { formatBytes } from '../../../lib/formatters'
import type { Attachment, MetadataItem } from '../../../lib/types'
import { kindLabel } from '../lib/fileKind'

/** Campos que ya están en la cabecera del visor y no se repiten. */
const REDUNDANT = new Set(['Archivo/Nombre', 'Archivo/Tamaño'])

function groupItems(items: MetadataItem[]): [string, MetadataItem[]][] {
  const groups = new Map<string, MetadataItem[]>()
  for (const item of items) {
    if (REDUNDANT.has(`${item.group}/${item.label}`)) continue
    groups.set(item.group, [...(groups.get(item.group) ?? []), item])
  }
  return [...groups.entries()]
}

/** Panel lateral del visor con las propiedades del adjunto que el backend pudo leer. */
export function AttachmentDetails({ attachment }: { attachment: Attachment }) {
  const groups = groupItems(attachment.metadata)
  return (
    <aside className="viewer-details" aria-label="Detalles del archivo">
      <h3>Detalles</h3>
      <dl>
        <div>
          <dt>Tipo</dt>
          <dd>{kindLabel(attachment.name, attachment.content_type)}</dd>
        </div>
        <div>
          <dt>Tamaño</dt>
          <dd>{formatBytes(attachment.size_bytes)}</dd>
        </div>
      </dl>
      {groups.map(([group, items]) => (
        <section key={group}>
          <h4>{group}</h4>
          <dl>
            {items.map((item, position) => (
              <div key={`${item.label}-${position}`}>
                <dt>{item.label}</dt>
                <dd>{item.value}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
      {groups.length === 0 && (
        <p className="viewer-details__empty">No hay más propiedades legibles de este archivo.</p>
      )}
    </aside>
  )
}
