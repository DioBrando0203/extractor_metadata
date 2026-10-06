import { QuestionCircle20Regular } from '@fluentui/react-icons'
import { StatusAlert } from '../../../components/ui/StatusAlert'

const STEPS = [
  {
    title: 'Abre los archivos',
    text: 'Arrastra uno o varios .msg a cualquier parte de la ventana, o usa “Abrir MSG”. Puedes buscar en la bandeja desde la barra superior.',
  },
  {
    title: 'Espera la lectura',
    text: 'Se procesan en orden. Si uno falla, los demás continúan y puedes reintentarlo después.',
  },
  {
    title: 'Lee el correo',
    text: 'Elige un elemento de la bandeja para ver remitente, destinatarios, fecha, texto y adjuntos.',
  },
  {
    title: 'Mira y descarga los adjuntos',
    text: 'Pulsa un adjunto para verlo de frente (imágenes, PDF, texto y la miniatura de planos AutoCAD) o usa el botón de descarga. El archivo original no se modifica.',
  },
]

export function HelpPage() {
  return (
    <article className="page" aria-labelledby="help-title">
      <p className="eyebrow eyebrow--brand">
        <QuestionCircle20Regular aria-hidden="true" /> Guía rápida
      </p>
      <h1 id="help-title">Cómo analizar un MSG</h1>
      <ol className="steps">
        {STEPS.map((step) => (
          <li key={step.title}>
            <strong>{step.title}</strong>
            <span>{step.text}</span>
          </li>
        ))}
      </ol>

      <h2>Qué significa “lectura parcial”</h2>
      <p>
        El archivo tiene partes dañadas o incompletas. Se muestra todo lo que sigue legible: puedes leer el
        texto disponible y descargar los adjuntos que aparezcan. No se reparan datos que ya no están en el
        archivo.
      </p>

      <h2>Si un archivo falla</h2>
      <p>
        Usa <b>Reintentar</b> en la bandeja. Si el error menciona la ruta o el nombre, copia el archivo a una
        carpeta con ruta corta, renómbralo y vuelve a abrirlo.
      </p>

      <StatusAlert tone="info" title="Privacidad">
        No hay cuentas ni historial. Los archivos sólo viven en la memoria de esta pestaña y el servicio local
        borra sus copias temporales al terminar cada lectura.
      </StatusAlert>
    </article>
  )
}
