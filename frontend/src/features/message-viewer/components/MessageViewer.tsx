import { useId, useState } from 'react'
import { Download, FileText, RefreshCw } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import { MetadataTable } from '../../../components/ui/MetadataTable'
import { StatusAlert } from '../../../components/ui/StatusAlert'
import { AttachmentList } from '../../attachments/components/AttachmentList'
import type { Message } from '../../../lib/types'
import { formatBytes, formatDate } from '../../../lib/formatters'

type Props = { message: Message; onChoose: () => void }
type Tab = 'Resumen' | 'Encabezados' | 'Cuerpo' | 'Adjuntos' | 'Metadatos'

function exportReport(message: Message) {
  const content = JSON.stringify({ exported_at: new Date().toISOString(), message }, null, 2)
  const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `${message.file_name.replace(/\.msg$/i, '') || 'informe'}-metadata.json`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function MessageViewer({ message, onChoose }: Props) {
  const [tab, setTab] = useState<Tab>('Resumen')
  const tabId = useId()
  const tabs: Tab[] = ['Resumen', 'Encabezados', 'Cuerpo', 'Adjuntos', 'Metadatos']
  return (
    <article className="message-reader">
      <div className="reader-toolbar">
        <p className="reader-toolbar__label">Resultado de extracción</p>
        <div>
          <Button variant="secondary" onClick={onChoose}>
            <RefreshCw size={16} /> Nuevo análisis
          </Button>
          <Button
            variant="ghost"
            aria-label="Exportar informe JSON"
            title="Exportar informe JSON"
            onClick={() => exportReport(message)}
          >
            <Download size={18} />
          </Button>
        </div>
      </div>
      <div className="message-title">
        <div>
          <span className="file-glyph">
            <FileText size={26} />
          </span>
          <h1>{message.subject || 'Mensaje sin asunto'}</h1>
        </div>
        <span className={`status-pill status-pill--${message.status}`}>
          {message.status === 'partial' ? 'Extracción parcial' : 'Extracción completa'}
        </span>
      </div>
      <div className="mail-header">
        <div className="avatar">{(message.sender || '?')[0].toUpperCase()}</div>
        <div>
          <strong>{message.sender || 'Remitente desconocido'}</strong>
          <p>
            {message.recipients.join(' · ') || 'Sin destinatarios'}{' '}
            <span>· {formatDate(message.sent_at)}</span>
          </p>
        </div>
        <span>{formatBytes(message.file_size_bytes)}</span>
      </div>
      {message.warnings.length > 0 && (
        <StatusAlert tone="warning" title="Observaciones del extractor">
          {message.warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </StatusAlert>
      )}
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
            <h2>Resumen del análisis</h2>
            <div className="summary-grid">
              <Info label="Archivo" value={message.file_name} />
              <Info label="Adjuntos" value={`${message.attachments.length} encontrados`} />
              <Info label="Cuerpo" value={message.body_preview ? 'Texto disponible' : 'Sin texto legible'} />
              <Info label="Estado" value={message.status === 'partial' ? 'Parcial' : 'Completada'} />
              {message.received_at && <Info label="Recepción" value={formatDate(message.received_at)} />}
            </div>
            <h2>Propiedades del mensaje</h2>
            <MetadataTable
              items={message.properties.filter((item) => item.group === 'Mensaje')}
              ariaLabel="Propiedades del mensaje"
              emptyMessage="Consulta la pestaña Metadatos para las propiedades recuperadas."
            />
          </section>
        )}
        {tab === 'Encabezados' && (
          <section className="summary">
            <h2>Encabezados disponibles</h2>
            <MetadataTable
              items={message.headers}
              ariaLabel="Encabezados del mensaje"
              emptyMessage="El extractor no devolvió encabezados legibles."
            />
          </section>
        )}
        {tab === 'Cuerpo' && (
          <section className="body-content">
            <h2>Contenido de texto</h2>
            {message.body_truncated && (
              <StatusAlert tone="info" title="Contenido abreviado">
                El extractor indicó que el cuerpo se truncó para mantener la lectura estable.
              </StatusAlert>
            )}
            <pre>{message.body_preview || 'No se pudo recuperar contenido de texto del mensaje.'}</pre>
          </section>
        )}
        {tab === 'Adjuntos' && <AttachmentList attachments={message.attachments} />}
        {tab === 'Metadatos' && (
          <section className="summary">
            <h2>Metadatos técnicos</h2>
            <MetadataTable items={message.properties} ariaLabel="Metadatos técnicos" />
          </section>
        )}
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
