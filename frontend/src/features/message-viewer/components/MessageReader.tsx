import { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowLeft20Regular, Mail16Regular } from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import { messageTitle, messageTrail } from '../../../lib/mail'
import type { Message } from '../../../lib/types'
import { MessageViewer } from './MessageViewer'

type Props = {
  message: Message
  file: File
  /** Términos de la búsqueda de la bandeja, para resaltarlos en el correo. */
  terms?: string[]
}

/**
 * Lector con navegación por correos adjuntos: abrir uno lo muestra como un correo propio y una barra
 * permite volver al que lo contiene. No pide nada nuevo: el backend ya leyó cada correo adjunto.
 */
export function MessageReader({ message, file, terms }: Props) {
  const [path, setPath] = useState<number[]>([])
  const [navigated, setNavigated] = useState(false)
  const trail = messageTrail(message, path)
  const depth = trail.length - 1
  // Misma referencia mientras no se navega: la caché de adjuntos depende de ella.
  const current = useMemo(() => path.slice(0, depth), [path, depth])
  const top = useRef<HTMLDivElement>(null)

  // Al cambiar de correo, la vista vuelve al inicio para que se vea la barra "Volver" y el asunto.
  useEffect(() => {
    if (navigated) scrollContainerToTop(top.current)
  }, [current, navigated])

  const go = (next: number[]) => {
    setPath(next)
    setNavigated(true)
  }

  return (
    <div ref={top}>
      {depth > 0 && <AttachedMessageBar parent={trail[depth - 1]} onBack={() => go(current.slice(0, -1))} />}
      <MessageViewer
        key={current.join('/')}
        message={trail[depth]}
        file={file}
        terms={terms}
        messagePath={current}
        onOpenMessage={(index) => go([...current, index])}
        focusTitle={navigated}
      />
    </div>
  )
}

/** Lleva al inicio el primer ancestro que se desplaza, sin depender de cómo está armado el layout. */
function scrollContainerToTop(element: HTMLElement | null) {
  for (let node = element?.parentElement; node; node = node.parentElement) {
    if (node.scrollHeight > node.clientHeight && getComputedStyle(node).overflowY !== 'visible') {
      node.scrollTop = 0
      return
    }
  }
}

function AttachedMessageBar({ parent, onBack }: { parent: Message; onBack: () => void }) {
  const title = messageTitle(parent.subject, parent.file_name).text
  return (
    <nav className="mail-trail" aria-label="Correo adjunto">
      <Button variant="subtle" size="sm" aria-label={`Volver a ${title}`} onClick={onBack}>
        <ArrowLeft20Regular aria-hidden="true" /> Volver
      </Button>
      <p className="mail-trail__text" title={title}>
        <Mail16Regular aria-hidden="true" />
        <span className="mail-trail__label">
          Correo adjunto en <span className="mail-trail__parent">{title}</span>
        </span>
      </p>
    </nav>
  )
}
