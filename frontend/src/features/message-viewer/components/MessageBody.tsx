import { useMemo } from 'react'
import { findRanges } from '../../../lib/textSearch'
import { splitThread } from '../../../lib/thread'
import type { Attachment } from '../../../lib/types'
import { useHighlightTerms } from '../highlight'
import { InlineContent } from './InlineContent'
import { QuotedThread } from './QuotedThread'

type Props = {
  text: string
  truncated: boolean
  attachments: Attachment[]
  onOpenAttachment: (index: number) => void
}

/** Cuerpo del correo: el mensaje actual con sus imágenes en posición y, debajo, el historial citado. */
export function MessageBody({ text, truncated, attachments, onOpenAttachment }: Props) {
  const terms = useHighlightTerms()
  const thread = useMemo(() => splitThread(text), [text])
  const hasCurrent = thread.current.trim().length > 0
  // Si lo buscado sólo está en el historial, se despliega para que la coincidencia se vea.
  const quotedMatch = thread.quoted.some(
    (message) =>
      findRanges(message.body, terms).length > 0 ||
      message.fields.some((field) => findRanges(field.value, terms).length > 0),
  )
  return (
    <section className="mail__body" aria-label="Contenido del correo">
      {!text && <p className="mail__empty">No se pudo recuperar el texto de este correo.</p>}
      {hasCurrent && (
        // Siempre texto plano: el HTML del correo nunca se inyecta en la página.
        <InlineContent text={thread.current} attachments={attachments} onOpenAttachment={onOpenAttachment} />
      )}
      {thread.quoted.length > 0 && (
        <QuotedThread
          key={quotedMatch ? 'con-coincidencias' : 'sin-coincidencias'}
          messages={thread.quoted}
          attachments={attachments}
          onOpenAttachment={onOpenAttachment}
          // Un reenvío sin texto propio abre el historial: es todo el contenido.
          defaultOpen={!hasCurrent || quotedMatch}
        />
      )}
      {truncated && <p className="mail__note">El mensaje es muy largo: se muestra sólo la primera parte.</p>}
    </section>
  )
}
