import { FolderOpen20Regular, Map24Regular } from '@fluentui/react-icons'
import { useRef, useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { convertGeodata, saveBlob } from '../../../lib/api'

const ACCEPT = '.kml,.kmz,application/vnd.google-earth.kml+xml,application/vnd.google-earth.kmz'

export function GeodataConverter() {
  const input = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File>()
  const [error, setError] = useState<string>()
  const [converting, setConverting] = useState(false)

  const choose = (candidate?: File) => {
    if (!candidate) return
    if (!/\.km[zl]$/i.test(candidate.name)) {
      setError('Selecciona un archivo KML o KMZ.')
      return
    }
    setError(undefined)
    setFile(candidate)
  }
  const convert = async () => {
    if (!file) return
    setConverting(true)
    setError(undefined)
    try {
      const result = await convertGeodata(file)
      saveBlob(result.blob, result.filename)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No fue posible convertir el archivo.')
    } finally {
      setConverting(false)
    }
  }

  return (
    <section className="geodata page" aria-labelledby="geodata-title">
      <Map24Regular className="geodata__icon" aria-hidden="true" />
      <h1 id="geodata-title">Conversor KMZ/KML</h1>
      <p>Convierte un archivo local a GeoPackage. El archivo se elimina al terminar la descarga.</p>
      <input
        ref={input}
        type="file"
        accept={ACCEPT}
        hidden
        onChange={(event) => choose(event.target.files?.[0])}
      />
      <div className="geodata__actions">
        <Button variant="secondary" onClick={() => input.current?.click()} disabled={converting}>
          <FolderOpen20Regular aria-hidden="true" /> {file ? 'Cambiar archivo' : 'Elegir KML o KMZ'}
        </Button>
        <Button onClick={convert} disabled={!file || converting}>
          {converting ? 'Convirtiendo…' : 'Convertir y descargar'}
        </Button>
      </div>
      {file && <p className="geodata__file">Archivo: {file.name}</p>}
      {error && (
        <p className="geodata__error" role="alert">
          {error}
        </p>
      )}
    </section>
  )
}
