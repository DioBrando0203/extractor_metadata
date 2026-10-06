import { Clock, LoaderCircle } from 'lucide-react'

type Props = { name: string; waiting: boolean }

/** Esqueleto del panel de lectura mientras el archivo espera turno o se está leyendo. */
export function MessageLoading({ name, waiting }: Props) {
  return (
    <article className="mail mail--loading" aria-busy="true">
      <div className="mail-loading__status" role="status">
        <span className="mail-loading__icon" aria-hidden="true">
          {waiting ? <Clock size={18} /> : <LoaderCircle size={18} className="spin" />}
        </span>
        <div>
          <h1>{waiting ? 'En espera' : 'Leyendo el correo'}</h1>
          <p>
            “{name}” {waiting ? 'se abrirá cuando terminen los archivos anteriores.' : 'se está procesando.'}
          </p>
        </div>
      </div>
      <div className="mail__head" aria-hidden="true">
        <span className="skeleton skeleton--title" />
        <div className="skeleton-sender">
          <span className="skeleton skeleton--avatar" />
          <div>
            <span className="skeleton skeleton--line" style={{ width: '38%' }} />
            <span className="skeleton skeleton--line" style={{ width: '56%' }} />
          </div>
        </div>
      </div>
      <div className="mail__body" aria-hidden="true">
        {[92, 84, 88, 60, 0, 90, 72].map((width, index) =>
          width ? (
            <span key={index} className="skeleton skeleton--line" style={{ width: `${width}%` }} />
          ) : (
            <span key={index} className="skeleton-gap" />
          ),
        )}
      </div>
    </article>
  )
}
