import {
  ArrowUpload24Regular,
  Attach20Regular,
  DocumentError20Regular,
  FolderOpen20Regular,
  LockClosed20Regular,
  ShieldCheckmark16Regular,
} from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'

type Props = {
  /** Hay archivos arrastrándose sobre la ventana; el destino real es toda la ventana. */
  active: boolean
  onBrowse: () => void
}

const FEATURES = [
  { icon: LockClosed20Regular, title: 'Local', text: 'Se procesa en este equipo; nada se sube a internet.' },
  {
    icon: Attach20Regular,
    title: 'Adjuntos',
    text: 'Ve imágenes, PDF y planos de frente y descarga cualquier archivo.',
  },
  {
    icon: DocumentError20Regular,
    title: 'Lectura parcial',
    text: 'Si el archivo está dañado, ves lo que siga legible.',
  },
]

export function Dropzone({ active, onBrowse }: Props) {
  return (
    <section className="landing" aria-labelledby="landing-title">
      <p className="eyebrow">
        <ShieldCheckmark16Regular aria-hidden="true" /> Privado · sin cuenta · sin base de datos
      </p>
      <h1 id="landing-title" className="landing__title">
        Cargar MSG
      </h1>
      <p className="landing__lead">
        Abre un archivo <b>.msg</b>, aunque esté dañado, para leer el correo y descargar sus adjuntos sin
        salir de tu equipo.
      </p>
      <div className={`dropzone ${active ? 'is-active' : ''}`}>
        <span className="dropzone__icon" aria-hidden="true">
          <ArrowUpload24Regular />
        </span>
        <p className="dropzone__title">
          {active ? 'Suelta los archivos para abrirlos' : 'Arrastra tus archivos .msg aquí'}
        </p>
        <p className="dropzone__or">o</p>
        <Button onClick={onBrowse}>
          <FolderOpen20Regular aria-hidden="true" /> Elegir archivos
        </Button>
        <p className="dropzone__hint">
          Puedes abrir varios a la vez. Los archivos grandes tardan más, pero no se rechazan por su peso.
        </p>
      </div>
      <ul className="landing__features">
        {FEATURES.map(({ icon: Icon, title, text }) => (
          <li key={title}>
            <Icon aria-hidden="true" />
            <strong>{title}</strong>
            <span>{text}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
