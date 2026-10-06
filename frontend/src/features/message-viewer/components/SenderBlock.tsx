import { Avatar } from '../../../components/ui/Avatar'
import { Highlight } from '../../../components/ui/Highlight'
import { formatMailDate } from '../../../lib/formatters'
import { groupRecipients, parseAddress } from '../../../lib/mail'
import type { Message } from '../../../lib/types'
import { useHighlightTerms } from '../highlight'
import { RecipientList } from './RecipientList'

/** Remitente, fecha y destinatarios del correo, como la cabecera de un mensaje en Outlook. */
export function SenderBlock({ message }: { message: Message }) {
  const terms = useHighlightTerms()
  const sender = message.sender ? parseAddress(message.sender) : null
  const recipients = groupRecipients(message.recipients)
  const dateValue = message.sent_at ?? message.received_at
  const date = formatMailDate(dateValue)
  return (
    <div className={`mail__sender ${recipients.length ? '' : 'mail__sender--compact'}`}>
      <Avatar name={sender?.name} />
      <div className="mail__sender-body">
        <div className="mail__sender-top">
          <p className="mail__from">
            {sender ? (
              <>
                <strong>
                  <Highlight text={sender.name} terms={terms} />
                </strong>
                {sender.email && sender.email !== sender.name && (
                  <span className="mail__email">
                    &lt;
                    <Highlight text={sender.email} terms={terms} />
                    &gt;
                  </span>
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
  )
}
