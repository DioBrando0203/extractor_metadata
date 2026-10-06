import { useState } from 'react'
import { ChevronDown16Regular, ChevronUp16Regular } from '@fluentui/react-icons'
import { Avatar } from '../../../components/ui/Avatar'
import { Button } from '../../../components/ui/Button'
import { splitAddresses } from '../../../lib/mail'
import type { QuotedField, QuotedMessage } from '../../../lib/thread'
import type { Attachment } from '../../../lib/types'
import { InlineContent } from './InlineContent'

type Props = {
  messages: QuotedMessage[]
  attachments: Attachment[]
  onOpenAttachment: (index: number) => void
  defaultOpen: boolean
}

/** Historial citado del hilo, plegado como en Outlook; cada mensaje muestra quién lo envió y cuándo. */
export function QuotedThread({ messages, attachments, onOpenAttachment, defaultOpen }: Props) {
  const [open, setOpen] = useState(defaultOpen)
  const count = messages.length
  return (
    <div className="thread">
      <Button variant="secondary" size="sm" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        {open ? <ChevronUp16Regular aria-hidden="true" /> : <ChevronDown16Regular aria-hidden="true" />}
        {open
          ? 'Ocultar mensajes anteriores'
          : `Mostrar ${count === 1 ? 'el mensaje anterior' : `los ${count} mensajes anteriores`}`}
      </Button>
      {open && (
        <ol className="thread__list">
          {messages.map((message, position) => (
            <li key={position}>
              <QuotedMessageView
                message={message}
                attachments={attachments}
                onOpenAttachment={onOpenAttachment}
              />
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

const DETAIL_FIELDS: QuotedField['label'][] = ['Para', 'CC', 'CCO', 'Asunto']

function QuotedMessageView({
  message,
  attachments,
  onOpenAttachment,
}: Omit<Props, 'messages' | 'defaultOpen'> & { message: QuotedMessage }) {
  const value = (label: QuotedField['label']) => message.fields.find((field) => field.label === label)?.value
  const sender = splitAddresses(value('De') ?? '')[0]
  const sent = value('Enviado')
  return (
    <article className="quoted" aria-label={`Mensaje de ${sender?.name ?? 'remitente desconocido'}`}>
      <header className="quoted__head">
        <Avatar name={sender?.name} size="sm" />
        <div className="quoted__who">
          <p className="quoted__from">
            <strong className={sender ? undefined : 'is-missing'}>
              {sender?.name ?? 'Remitente desconocido'}
            </strong>
            {sender?.email && sender.email !== sender.name && (
              <span className="quoted__email">&lt;{sender.email}&gt;</span>
            )}
          </p>
          {DETAIL_FIELDS.map((label) => {
            const text = value(label)
            if (!text) return null
            // Como en la cabecera principal: nombres visibles y la lista completa al pasar el ratón.
            const people = label !== 'Asunto'
            const shown = people
              ? splitAddresses(text)
                  .map((address) => address.name)
                  .join('; ')
              : text
            return (
              <p key={label} className="quoted__field" title={people ? text : undefined}>
                <span>{label}:</span> {shown}
              </p>
            )
          })}
        </div>
        {sent && <span className="quoted__date">{sent}</span>}
      </header>
      {message.body && (
        <InlineContent text={message.body} attachments={attachments} onOpenAttachment={onOpenAttachment} />
      )}
    </article>
  )
}
