import { useId, useMemo, useState } from 'react'
import { DocumentText16Regular } from '@fluentui/react-icons'
import { Tabs } from '../../../components/ui/Tabs'
import { AttachmentList } from '../../attachments/components/AttachmentList'
import { AttachmentViewer } from '../../attachments/components/AttachmentViewer'
import { useAttachmentFiles } from '../../attachments/hooks/useAttachmentFiles'
import { formatBytes, tidyText } from '../../../lib/formatters'
import { messageTitle } from '../../../lib/mail'
import { findRanges } from '../../../lib/textSearch'
import { inlineAttachmentIndices } from '../../../lib/thread'
import type { Message } from '../../../lib/types'
import { HighlightContext } from '../highlight'
import { MessageBody } from './MessageBody'
import { MessageTitle } from './MessageTitle'
import { SenderBlock } from './SenderBlock'

type Props = {
  message: Message
  file: File
  /** Términos de la búsqueda de la bandeja, para resaltarlos en el correo. */
  terms?: string[]
}
type Tab = 'message' | 'attachments'

/**
 * Panel de lectura con la estructura de Outlook: asunto y, debajo, la tarjeta del mensaje. Si el cuerpo
 * coloca imágenes en su posición, la pestaña "Datos adjuntos" reúne además todos los archivos.
 */
export function MessageViewer({ message, file, terms = [] }: Props) {
  const titleId = useId()
  const panelId = useId()
  const files = useAttachmentFiles(file)
  const [tab, setTab] = useState<Tab>('message')
  const [viewing, setViewing] = useState<number | null>(null)
  const { attachments } = message
  const body = tidyText(message.body_preview)
  const title = messageTitle(message.subject, message.file_name, body)
  const inline = useMemo(() => inlineAttachmentIndices(body, attachments), [body, attachments])
  const wellIndices = attachments.map((_, index) => index).filter((index) => !inline.has(index))
  const tabbed = inline.size > 0
  const showGallery = tabbed && tab === 'attachments'
  const hits = useMemo(
    () => findRanges([title.text, message.sender ?? '', ...message.recipients, body].join(' '), terms).length,
    [title.text, message.sender, message.recipients, body, terms],
  )

  return (
    <HighlightContext.Provider value={terms}>
      <article className="mail" aria-labelledby={titleId}>
        <MessageTitle
          id={titleId}
          text={title.text}
          source={title.source}
          partial={message.status === 'partial'}
          hits={hits}
        />
        <div className="mail__card">
          <SenderBlock message={message} />
          {tabbed && (
            <Tabs
              label="Vista del correo"
              panelId={panelId}
              selected={tab}
              onSelect={(id) => setTab(id as Tab)}
              tabs={[
                { id: 'message', label: 'Mensaje' },
                { id: 'attachments', label: `Datos adjuntos (${attachments.length})` },
              ]}
            />
          )}
          <div
            id={tabbed ? panelId : undefined}
            role={tabbed ? 'tabpanel' : undefined}
            aria-labelledby={tabbed ? `${panelId}-${tab}` : undefined}
          >
            {showGallery ? (
              <AttachmentList
                attachments={attachments}
                files={files}
                onOpen={setViewing}
                collapsible={false}
                heading={`Todos los datos adjuntos (${attachments.length})`}
              />
            ) : (
              <>
                {wellIndices.length > 0 && (
                  <AttachmentList
                    attachments={attachments}
                    indices={wellIndices}
                    files={files}
                    onOpen={setViewing}
                  />
                )}
                <MessageBody
                  text={body}
                  truncated={message.body_truncated}
                  attachments={attachments}
                  onOpenAttachment={setViewing}
                />
              </>
            )}
          </div>
          <footer className="mail__foot">
            <DocumentText16Regular aria-hidden="true" />
            <span className="mail__foot-name">{message.file_name}</span>
            <span aria-hidden="true">·</span>
            <span>{formatBytes(message.file_size_bytes)}</span>
          </footer>
        </div>
        {viewing !== null && (
          <AttachmentViewer
            attachments={attachments}
            index={viewing}
            files={files}
            onNavigate={setViewing}
            onClose={() => setViewing(null)}
          />
        )}
      </article>
    </HighlightContext.Provider>
  )
}
