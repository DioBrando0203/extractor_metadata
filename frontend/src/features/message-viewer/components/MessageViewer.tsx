import { useId, useState } from 'react'
import { FileText, TriangleAlert } from 'lucide-react'
import { Avatar } from '../../../components/ui/Avatar'
import { AttachmentList } from '../../attachments/components/AttachmentList'
import { formatBytes, formatMailDate, tidyText } from '../../../lib/formatters'
import { groupRecipients, messageTitle, parseAddress } from '../../../lib/mail'
import type { RecipientGroup } from '../../../lib/mail'
import type { Message } from '../../../lib/types'

type Props = { message: Message; file: File }

/** Panel de lectura: encabezado, adjuntos y cuerpo en una sola vista, como un lector de correo. */
export function MessageViewer({ message, file }: Props) {
  const titleId = useId()
  const title = messageTitle(message.subject, message.file_name)
  const sender = message.sender ? parseAddress(message.sender) : null
  const recipients = groupRecipients(message.recipients)
  const dateValue = message.sent_at ?? message.received_at
  const date = formatMailDate(dateValue)

  return (
    <article className="mail" aria-labelledby={titleId}>
      <header className="mail__head">
        <h1 id={titleId} className="mail__subject">
          {title.text}
        </h1>
        {title.fromFileName && (
          <p className="mail__subject-note">Asunto no recuperado: se muestra el nombre del archivo.</p>
        )}
        {message.status === 'partial' && (
          <p className="mail__infobar">
            <TriangleAlert size={16} aria-hidden="true" />
            <span>
              <strong>Lectura parcial.</strong> Es posible que falten algunos datos de este correo; se muestra
              todo lo que se pudo leer.
            </span>
          </p>
        )}
        <div className={`mail__sender ${recipients.length ? '' : 'mail__sender--compact'}`}>
          <Avatar name={sender?.name} />
          <div className="mail__sender-body">
            <div className="mail__sender-top">
              <p className="mail__from">
                {sender ? (
                  <>
                    <strong>{sender.name}</strong>
                    {sender.email && sender.email !== sender.name && (
                      <span className="mail__email">&lt;{sender.email}&gt;</span>
                    )}
                  </>
                ) : (
                  <strong className="is-missing">Remitente desconocido</strong>
                )}
              </p>
              {date && dateValue && (
                <time className="mail__date" dateTime={dateValue}>
                  {date}
                </time>
              )}
            </div>
            {recipients.length > 0 && (
              <dl className="mail__recipients">
                {recipients.map((group) => (
                  <RecipientRow key={group.label} group={group} />
                ))}
              </dl>
            )}
          </div>
        </div>
      </header>

      {message.attachments.length > 0 && <AttachmentList attachments={message.attachments} file={file} />}

      <section className="mail__body" aria-label="Contenido del correo">
        <MessageBody text={message.body_preview} truncated={message.body_truncated} />
      </section>

      <footer className="mail__foot">
        <FileText size={14} aria-hidden="true" />
        <span className="mail__foot-name">{message.file_name}</span>
        <span aria-hidden="true">·</span>
        <span>{formatBytes(message.file_size_bytes)}</span>
      </footer>
    </article>
  )
}

const VISIBLE_RECIPIENTS = 8

function RecipientRow({ group }: { group: RecipientGroup }) {
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? group.addresses : group.addresses.slice(0, VISIBLE_RECIPIENTS)
  const hidden = group.addresses.length - visible.length
  return (
    <div className="mail__recipient-row">
      <dt>{group.label}:</dt>
      <dd>
        {visible.map((address, index) => (
          <span key={`${address.name}-${index}`} className="recipient" title={address.email ?? undefined}>
            {address.name}
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

function MessageBody({ text, truncated }: { text?: string | null; truncated: boolean }) {
  const body = tidyText(text)
  return (
    <>
      {body ? (
        // Siempre texto plano: el HTML del correo nunca se inyecta en la página.
        <pre className="mail__text">{body}</pre>
      ) : (
        <p className="mail__empty">No se pudo recuperar el texto de este correo.</p>
      )}
      {truncated && <p className="mail__note">El mensaje es muy largo: se muestra sólo la primera parte.</p>}
    </>
  )
}
