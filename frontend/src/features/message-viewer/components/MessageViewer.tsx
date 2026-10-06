import { useId, useState } from 'react'
import { FileText, RefreshCw } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import { AttachmentList } from '../../attachments/components/AttachmentList'
import type { Message } from '../../../lib/types'
import { formatBytes, formatDate } from '../../../lib/formatters'

type Props = { message: Message; file: File; onChoose: () => void }
type Tab = 'Resumen' | 'Cuerpo' | 'Adjuntos'

export function MessageViewer({ message, file, onChoose }: Props) {
  const [tab, setTab] = useState<Tab>('Resumen')
  const tabId = useId()
  const tabs: Tab[] = ['Resumen', 'Cuerpo', 'Adjuntos']
  return (
    <article className="message-reader">
      <div className="reader-toolbar">
        <p className="reader-toolbar__label">Correo recuperado</p>
        <Button variant="secondary" onClick={onChoose}>
          <RefreshCw size={16} /> Nuevo analisis
        </Button>
      </div>
      <div className="message-title">
        <div>
          <span className="file-glyph">
            <FileText size={26} />
          </span>
          <h1>{message.subject || 'Mensaje sin asunto'}</h1>
        </div>
        <span className={`status-pill status-pill--${message.status}`}>
          {message.status === 'partial' ? 'Recuperado parcialmente' : 'Correo listo'}
        </span>
      </div>
      <div className="mail-header">
        <div className="avatar">{(message.sender || '?')[0].toUpperCase()}</div>
        <div>
          <strong>{message.sender || 'Remitente desconocido'}</strong>
          <p>
            {message.recipients.join(' | ') || 'Sin destinatarios'}{' '}
            <span>| {formatDate(message.sent_at)}</span>
          </p>
        </div>
        <span>{formatBytes(message.file_size_bytes)}</span>
      </div>
      <div className="tabs" role="tablist" aria-label="Contenido del mensaje">
        {tabs.map((item, index) => (
          <button
            key={item}
            id={`${tabId}-${item}`}
            role="tab"
            tabIndex={tab === item ? 0 : -1}
            aria-selected={tab === item}
            aria-controls={`${tabId}-panel-${item}`}
            className={tab === item ? 'active' : ''}
            onClick={() => setTab(item)}
            onKeyDown={(event) => {
              const current = tabs.indexOf(tab)
              const next =
                event.key === 'Home'
                  ? 0
                  : event.key === 'End'
                    ? tabs.length - 1
                    : event.key === 'ArrowRight'
                      ? (current + 1) % tabs.length
                      : event.key === 'ArrowLeft'
                        ? (current - 1 + tabs.length) % tabs.length
                        : index
              if (next !== index || ['Home', 'End'].includes(event.key)) {
                event.preventDefault()
                setTab(tabs[next])
                document.getElementById(`${tabId}-${tabs[next]}`)?.focus()
              }
            }}
          >
            {item}
            {item === 'Adjuntos' && ` (${message.attachments.length})`}
          </button>
        ))}
      </div>
      <div id={`${tabId}-panel-${tab}`} role="tabpanel" aria-labelledby={`${tabId}-${tab}`} tabIndex={0}>
        {tab === 'Resumen' && (
          <section className="summary">
            <h2>Resumen</h2>
            <div className="summary-grid">
              <Info label="Archivo" value={message.file_name} />
              <Info label="Adjuntos" value={`${message.attachments.length} encontrados`} />
              <Info label="Mensaje" value={message.body_preview ? 'Texto disponible' : 'Sin texto legible'} />
              {message.received_at && <Info label="Recibido" value={formatDate(message.received_at)} />}
            </div>
          </section>
        )}
        {tab === 'Cuerpo' && (
          <section className="body-content">
            <h2>Mensaje</h2>
            {message.body_truncated && <p className="content-note">Se muestra una parte del mensaje.</p>}
            <pre>{message.body_preview || 'No se pudo recuperar contenido de texto del mensaje.'}</pre>
          </section>
        )}
        {tab === 'Adjuntos' && <AttachmentList attachments={message.attachments} file={file} />}
      </div>
    </article>
  )
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div className="info-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
