import { Certificate16Regular } from '@fluentui/react-icons'
import { StatusAlert } from '../../../components/ui/StatusAlert'
import type { Security } from '../../../lib/types'

const ALERTS = {
  opaque: {
    tone: 'info',
    title: 'Firmado en formato opaco.',
    text: 'El contenido viaja dentro de smime.p7m y esta aplicación no lo desempaqueta. Descárgalo y ábrelo con Outlook.',
  },
  encrypted: {
    tone: 'warning',
    title: 'Correo cifrado.',
    text: 'Sólo puede leerlo quien tiene la clave del destinatario, en su Outlook. Aquí se ven el remitente, el asunto, la fecha y el archivo cifrado (smime.p7m).',
  },
  protected: {
    tone: 'warning',
    title: 'Correo con permisos.',
    text: 'Su contenido está protegido (IRM) y sólo se abre en Outlook con una cuenta autorizada. Aquí se ven el remitente, el asunto y la fecha.',
  },
} as const

/**
 * Aviso de un correo S/MIME. La firma nunca se verifica aquí y así se dice; un correo opaco o cifrado
 * explica por qué no se ve su contenido y qué hacer.
 */
export function SecurityNote({ security }: { security?: Security | null }) {
  if (security === 'signed') {
    return (
      <p className="mail__security">
        <Certificate16Regular aria-hidden="true" />
        <span>
          <strong>Firmado digitalmente.</strong> Esta aplicación no comprueba la firma.
        </span>
      </p>
    )
  }
  const alert = security ? ALERTS[security] : null
  if (!alert) return null
  return (
    <div className="mail__notice">
      <StatusAlert tone={alert.tone} title={alert.title}>
        {alert.text}
      </StatusAlert>
    </div>
  )
}
