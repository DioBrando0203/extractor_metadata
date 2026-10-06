import { Warning20Filled } from '@fluentui/react-icons'
import { Highlight } from '../../../components/ui/Highlight'
import type { TitleSource } from '../../../lib/mail'
import { useHighlightTerms } from '../highlight'

type Props = {
  id: string
  text: string
  source: TitleSource
  partial: boolean
  /** Coincidencias de la búsqueda activa dentro del correo. */
  hits: number
}

const SOURCE_NOTE: Record<Exclude<TitleSource, 'subject'>, string> = {
  inferred: 'Asunto deducido del mensaje citado; coincide con el nombre del archivo.',
  file: 'Asunto no recuperado: se muestra el nombre del archivo.',
}

/** Asunto sobre la tarjeta del mensaje, nota de origen y aviso de lectura parcial. */
export function MessageTitle({ id, text, source, partial, hits }: Props) {
  const terms = useHighlightTerms()
  return (
    <>
      <header className="mail__subject-bar">
        <h1 id={id} className="mail__subject">
          <Highlight text={text} terms={terms} />
        </h1>
        {source !== 'subject' && <p className="mail__subject-note">{SOURCE_NOTE[source]}</p>}
        {terms.length > 0 && (
          <p className="mail__search-hits" role="status">
            {hits === 1 ? '1 coincidencia' : `${hits} coincidencias`} de la búsqueda en este correo
          </p>
        )}
      </header>
      {partial && (
        <p className="mail__infobar">
          <Warning20Filled className="mail__infobar-icon" aria-hidden="true" />
          <span>
            <strong>Lectura parcial.</strong> Es posible que falten algunos datos de este correo; se muestra
            todo lo que se pudo leer.
          </span>
        </p>
      )}
    </>
  )
}
