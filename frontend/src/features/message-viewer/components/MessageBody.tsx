import { useMemo } from 'react'
import { splitThread } from '../../../lib/thread'
import type { Attachment } from '../../../lib/types'
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
  const thread = useMemo(() => splitThread(text), [text])
  const hasCurrent = thread.current.trim().length > 0
  return (
    <section className="mail__body" aria-label="Contenido del correo">
      {!text && <p className="mail__empty">No se pudo recuperar el texto de este correo.</p>}
      {hasCurrent && (
        // Siempre texto plano: el HTML del correo nunca se inyecta en la página.
        <InlineContent text={thread.current} attachments={attachments} onOpenAttachment={onOpenAttachment} />
      )}
      {thread.quoted.length > 0 && (
        <QuotedThread
          messages={thread.quoted}
          attachments={attachments}
          onOpenAttachment={onOpenAttachment}
          // Un reenvío sin texto propio abre el historial: es todo el contenido.
          defaultOpen={!hasCurrent}
        />
      )}
      {truncated && <p className="mail__note">El mensaje es muy largo: se muestra sólo la primera parte.</p>}
    </section>
  )
}
