import { Map24Regular, MailInbox24Regular } from '@fluentui/react-icons'

type Props = { onChoose: (tool: 'inspector' | 'geodata') => void }

export function ToolPicker({ onChoose }: Props) {
  return (
    <section className="tools page" aria-labelledby="tools-title">
      <h1 id="tools-title">Herramientas</h1>
      <p>Elige una herramienta local para continuar.</p>
      <div className="tools__grid">
        <button type="button" className="tools__card" onClick={() => onChoose('inspector')}>
          <MailInbox24Regular aria-hidden="true" />
          <strong>Inspector MSG</strong>
          <span>Abre correos MSG y sus adjuntos.</span>
        </button>
        <button type="button" className="tools__card" onClick={() => onChoose('geodata')}>
          <Map24Regular aria-hidden="true" />
          <strong>Conversor KMZ/KML</strong>
          <span>Convierte archivos geográficos a GeoPackage.</span>
        </button>
      </div>
    </section>
  )
}
