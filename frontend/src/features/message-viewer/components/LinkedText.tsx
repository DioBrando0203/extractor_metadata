import { Highlight } from '../../../components/ui/Highlight'
import { splitLinks } from '../../../lib/links'

type Props = { text: string; terms: string[] }

/**
 * Texto con sus direcciones web como enlaces y la búsqueda resaltada. El enlace es la dirección visible
 * (nunca un destino oculto) y se abre en otra pestaña sin enviar de dónde viene.
 */
export function LinkedText({ text, terms }: Props) {
  return (
    <>
      {splitLinks(text).map((segment, index) =>
        segment.link ? (
          <a key={index} className="text-link" href={segment.link} target="_blank" rel="noopener noreferrer">
            <Highlight text={segment.text} terms={terms} />
          </a>
        ) : (
          <Highlight key={index} text={segment.text} terms={terms} />
        ),
      )}
    </>
  )
}
