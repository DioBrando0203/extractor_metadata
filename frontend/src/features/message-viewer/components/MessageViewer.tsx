import { useId } from 'react'
import { DocumentText16Regular, Warning20Filled } from '@fluentui/react-icons'
import { Avatar } from '../../../components/ui/Avatar'
import { AttachmentList } from '../../attachments/components/AttachmentList'
import { formatBytes, formatMailDate, tidyText } from '../../../lib/formatters'
import { groupRecipients, messageTitle, parseAddress } from '../../../lib/mail'
import type { Message } from '../../../lib/types'
import { RecipientList } from './RecipientList'

type Props = { message: Message; file: File }

/**
 * Panel de lectura con la estructura de un cliente de correo: el asunto arriba y, debajo, la tarjeta del
 * mensaje con remitente, destinatarios, fecha, adjuntos y cuerpo.
 */
export function MessageViewer({ message, file }: Props) {
  const titleId = useId()
  const title = messageTitle(message.subject, message.file_name)
  const sender = message.sender ? parseAddress(message.sender) : null
  const recipients = groupRecipients(message.recipients)
  const dateValue = message.sent_at ?? message.received_at
  const date = formatMailDate(dateValue)
  const body = tidyText(message.body_preview)

  return (
    <article className="mail" aria-labelledby={titleId}>
      <header className="mail__subject-bar">
        <h1 id={titleId} className="mail__subject">
          {title.text}
        </h1>
        {title.fromFileName && (
          <p className="mail__subject-note">Asunto no recuperado: se muestra el nombre del archivo.</p>
        )}
      </header>
      {message.status === 'partial' && (
        <p className="mail__infobar">
          <Warning20Filled className="mail__infobar-icon" aria-hidden="true" />
          <span>
            <strong>Lectura parcial.</strong> Es posible que falten algunos datos de este correo; se muestra
            todo lo que se pudo leer.
          </span>
        </p>
      )}
      <div className="mail__card">
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
            {recipients.length > 0 && <RecipientList groups={recipients} />}
          </div>
        </div>

        {message.attachments.length > 0 && <AttachmentList attachments={message.attachments} file={file} />}

        <section className="mail__body" aria-label="Contenido del correo">
          {body ? (
            // Siempre texto plano: el HTML del correo nunca se inyecta en la página.
            <pre className="mail__text">{body}</pre>
          ) : (
            <p className="mail__empty">No se pudo recuperar el texto de este correo.</p>
          )}
          {message.body_truncated && (
            <p className="mail__note">El mensaje es muy largo: se muestra sólo la primera parte.</p>
          )}
        </section>

        <footer className="mail__foot">
          <DocumentText16Regular aria-hidden="true" />
          <span className="mail__foot-name">{message.file_name}</span>
          <span aria-hidden="true">·</span>
          <span>{formatBytes(message.file_size_bytes)}</span>
        </footer>
      </div>
    </article>
  )
}
