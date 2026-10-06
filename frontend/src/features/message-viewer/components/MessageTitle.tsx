import { Warning20Filled } from '@fluentui/react-icons'
import type { TitleSource } from '../../../lib/mail'

type Props = { id: string; text: string; source: TitleSource; partial: boolean }

const SOURCE_NOTE: Record<Exclude<TitleSource, 'subject'>, string> = {
  inferred: 'Asunto deducido del mensaje citado; coincide con el nombre del archivo.',
  file: 'Asunto no recuperado: se muestra el nombre del archivo.',
}

/** Asunto sobre la tarjeta del mensaje, nota de origen y aviso de lectura parcial. */
export function MessageTitle({ id, text, source, partial }: Props) {
  return (
    <>
      <header className="mail__subject-bar">
        <h1 id={id} className="mail__subject">
          {text}
        </h1>
        {source !== 'subject' && <p className="mail__subject-note">{SOURCE_NOTE[source]}</p>}
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
