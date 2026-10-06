import { useState } from 'react'
import { Highlight } from '../../../components/ui/Highlight'
import type { RecipientGroup } from '../../../lib/mail'
import { useHighlightTerms } from '../highlight'

/** Más destinatarios que este número por fila se pliegan detrás de "+N más". */
const VISIBLE_RECIPIENTS = 8

/** Filas Para, CC y CCO: nombre visible y correo en el título, como en un cliente de correo. */
export function RecipientList({ groups }: { groups: RecipientGroup[] }) {
  return (
    <dl className="mail__recipients">
      {groups.map((group) => (
        <RecipientRow key={group.label} group={group} />
      ))}
    </dl>
  )
}

function RecipientRow({ group }: { group: RecipientGroup }) {
  const terms = useHighlightTerms()
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? group.addresses : group.addresses.slice(0, VISIBLE_RECIPIENTS)
  const hidden = group.addresses.length - visible.length
  return (
    <div className="mail__recipient-row">
      <dt>{group.label}:</dt>
      <dd>
        {visible.map((address, index) => (
          <span key={`${address.name}-${index}`} className="recipient" title={address.email ?? undefined}>
            <Highlight text={address.name} terms={terms} />
            {index < visible.length - 1 && '; '}
          </span>
        ))}
        {hidden > 0 && (
          <>
            {' '}
            <button
              type="button"
              className="link-button"
              aria-label={`+${hidden} más, mostrar todos los destinatarios`}
              onClick={() => setExpanded(true)}
            >
              +{hidden} más
            </button>
          </>
        )}
      </dd>
    </div>
  )
}
