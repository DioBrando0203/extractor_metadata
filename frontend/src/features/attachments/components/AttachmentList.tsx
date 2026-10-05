import { File, Paperclip, TriangleAlert } from 'lucide-react'
import { MetadataTable } from '../../../components/ui/MetadataTable'
import type { Attachment } from '../../../lib/types'
import { formatBytes } from '../../../lib/formatters'

type Props = { attachments: Attachment[] }
export function AttachmentList({ attachments }: Props) {
  return (
    <section className="attachments" aria-labelledby="attachments-title">
      <h2 id="attachments-title">Adjuntos detectados</h2>
      {attachments.length === 0 ? (
        <p className="empty-content">Este mensaje no incluye adjuntos legibles.</p>
      ) : (
        attachments.map((attachment, index) => (
          <details key={`${attachment.name}-${index}`} className="attachment">
            <summary>
              <span className="attachment-icon">
                <Paperclip size={19} />
              </span>
              <span>
                <strong>{attachment.name}</strong>
                <small>
                  {attachment.content_type || 'Tipo no identificado'} · {formatBytes(attachment.size_bytes)}
                </small>
              </span>
              <span className="metadata-count">{attachment.metadata.length} campos</span>
            </summary>
            {attachment.warnings.map((warning) => (
              <p className="inline-warning" key={warning}>
                <TriangleAlert size={14} /> {warning}
              </p>
            ))}
            <div className="attachment__detail">
              <File size={16} aria-hidden="true" />
              <MetadataTable
                items={attachment.metadata}
                ariaLabel={`Metadatos de ${attachment.name}`}
                emptyMessage="El extractor no devolvió metadatos para este adjunto."
              />
            </div>
          </details>
        ))
      )}
    </section>
  )
}
