import { Upload } from 'lucide-react'

/** Indicador visual mientras se arrastran archivos sobre la bandeja; no intercepta el evento drop. */
export function DropOverlay() {
  return (
    <div className="drop-overlay" aria-hidden="true">
      <div className="drop-overlay__card">
        <Upload size={28} />
        <strong>Suelta los archivos .msg</strong>
        <span>Se agregarán a la bandeja y se abrirán en orden.</span>
      </div>
    </div>
  )
}
