import { Download, LoaderCircle, Paperclip } from 'lucide-react'
import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { formatBytes } from '../../../lib/formatters'
import { downloadAttachment } from '../../../lib/api'
import type { Attachment } from '../../../lib/types'

type Props = { attachments: Attachment[]; file: File }

export function AttachmentList({ attachments, file }: Props) {
  const [downloading, setDownloading] = useState<number | null>(null)
  const [downloadError, setDownloadError] = useState<number | null>(null)

  async function download(attachment: Attachment, index: number) {
    setDownloading(index)
    setDownloadError(null)
    try {
      await downloadAttachment(file, index, attachment.name)
    } catch {
      setDownloadError(index)
    } finally {
      setDownloading(null)
    }
  }

  return (
    <section className="attachments" aria-labelledby="attachments-title">
      <h2 id="attachments-title">Archivos adjuntos</h2>
      {attachments.length === 0 ? (
        <p className="empty-content">Este mensaje no incluye archivos que se puedan abrir.</p>
      ) : (
        attachments.map((attachment, index) => (
          <article key={`${attachment.name}-${index}`} className="attachment">
            <div className="attachment__row">
              <span className="attachment-icon">
                <Paperclip size={19} />
              </span>
              <span>
                <strong>{attachment.name}</strong>
                <small>
                  {attachment.content_type || 'Tipo no identificado'} | {formatBytes(attachment.size_bytes)}
                </small>
              </span>
              <Button
                variant="secondary"
                className="attachment__download"
                onClick={() => void download(attachment, index)}
                disabled={downloading === index}
                title={`Descargar ${attachment.name}`}
              >
                {downloading === index ? <LoaderCircle className="spin" size={16} /> : <Download size={16} />}
                Descargar
              </Button>
            </div>
            {downloadError === index && (
              <p className="attachment__error">No se pudo descargar este archivo.</p>
            )}
          </article>
        ))
      )}
    </section>
  )
}
