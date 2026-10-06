import { Image20Regular, ImageOff20Regular } from '@fluentui/react-icons'
import { findInlineAttachment, parseInline } from '../../../lib/thread'
import type { Attachment } from '../../../lib/types'

type Props = { text: string; attachments: Attachment[]; onOpenAttachment: (index: number) => void }

/** Una o más líneas en blanco separan párrafos. */
const PARAGRAPH_BREAK = /\n{2,}/

/**
 * Texto del correo con las imágenes incrustadas en su posición. El texto siempre se muestra como
 * texto plano; cada imagen es la miniatura del adjunto y abre el visor al pulsarla.
 */
export function InlineContent({ text, attachments, onOpenAttachment }: Props) {
  return (
    <>
      {parseInline(text).map((part, position) =>
        part.kind === 'text' ? (
          <Paragraphs key={position} text={part.text} />
        ) : (
          <InlineImage
            key={position}
            cid={part.cid}
            attachments={attachments}
            onOpenAttachment={onOpenAttachment}
          />
        ),
      )}
    </>
  )
}

/**
 * Párrafos separados por líneas en blanco, con un espaciado compacto en lugar de una línea vacía
 * completa (Outlook deja una en blanco entre cada línea al convertir HTML a texto).
 */
function Paragraphs({ text }: { text: string }) {
  return (
    <div className="mail__text">
      {text.split(PARAGRAPH_BREAK).map((paragraph, index) => (
        <p key={index}>{paragraph}</p>
      ))}
    </div>
  )
}

function InlineImage({ cid, attachments, onOpenAttachment }: Omit<Props, 'text'> & { cid: string }) {
  const index = findInlineAttachment(cid, attachments)
  const attachment = attachments[index]
  if (!attachment) {
    return (
      <p className="inline-missing">
        <ImageOff20Regular aria-hidden="true" /> Imagen incrustada no disponible
      </p>
    )
  }
  if (!attachment.preview) {
    return (
      <button type="button" className="inline-file" onClick={() => onOpenAttachment(index)}>
        <Image20Regular aria-hidden="true" /> {attachment.name}
      </button>
    )
  }
  return (
    <button
      type="button"
      className="inline-image"
      aria-label={`Ver ${attachment.name}`}
      onClick={() => onOpenAttachment(index)}
    >
      <img src={attachment.preview} alt="" loading="lazy" decoding="async" />
    </button>
  )
}
