import {
  CalendarCancel20Regular,
  CalendarCheckmark20Regular,
  CalendarLtr20Regular,
  ContactCard20Regular,
  TaskListLtr20Regular,
} from '@fluentui/react-icons'
import type { FluentIcon } from '@fluentui/react-icons'
import { Highlight } from '../../../components/ui/Highlight'
import type { ItemDetails, ItemKind } from '../../../lib/types'
import { useHighlightTerms } from '../highlight'
import { ITEM_TITLES, itemRows } from '../lib/itemRows'

const ICONS: Record<ItemKind, FluentIcon> = {
  meeting: CalendarLtr20Regular,
  cancellation: CalendarCancel20Regular,
  response: CalendarCheckmark20Regular,
  appointment: CalendarLtr20Regular,
  contact: ContactCard20Regular,
  task: TaskListLtr20Regular,
}

/** Datos de una reunión, cita, contacto o tarea, como la cabecera de ese elemento en Outlook. */
export function ItemCard({ item }: { item: ItemDetails }) {
  const terms = useHighlightTerms()
  const Icon = ICONS[item.kind]
  const title = ITEM_TITLES[item.kind]
  return (
    <section className="item-card" aria-label={title} data-kind={item.kind}>
      <h2 className="item-card__title">
        <Icon aria-hidden="true" /> {title}
      </h2>
      <dl className="item-card__rows">
        {itemRows(item).map((row) => (
          <div key={row.label}>
            <dt>{row.label}</dt>
            <dd>
              <Highlight text={row.value} terms={terms} />
            </dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
