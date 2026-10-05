import { useRef, useState } from 'react'
import { FileUp, ShieldCheck } from 'lucide-react'
import { Button } from '../../../components/ui/Button'
import { StatusAlert } from '../../../components/ui/StatusAlert'

type Props = { busy: boolean; errors: string[]; onFiles: (files: File[]) => void }
export function Dropzone({ busy, errors, onFiles }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  function accept(files: FileList | null) {
    if (files?.length) onFiles(Array.from(files))
  }
  return (
    <div className="empty-reader">
      <div className="eyebrow">
        <ShieldCheck size={16} /> Privado · sin cuenta · sin base de datos
      </div>
      <h1>Lee lo que Outlook no pudo</h1>
      <p>
        Arrastra un archivo <b>.msg</b> o selecciónalo. Verás el mensaje, sus adjuntos y los metadatos
        disponibles en una sola vista.
      </p>
      <div
        className={`dropzone ${dragging ? 'dragging' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          accept(event.dataTransfer.files)
        }}
      >
        <FileUp size={38} />
        <strong>{busy ? 'La cola se está procesando' : 'Suelta tus archivos MSG aquí'}</strong>
        <span>Puedes elegir uno o varios archivos</span>
        <Button onClick={() => input.current?.click()}>Buscar archivos</Button>
        <input
          ref={input}
          type="file"
          multiple
          accept=".msg,application/vnd.ms-outlook"
          onChange={(event) => {
            accept(event.target.files)
            event.target.value = ''
          }}
          hidden
        />
      </div>
      {errors.map((error) => (
        <StatusAlert key={error} tone="error" title="No se pudo analizar un archivo.">
          {error} Si sospechas de una ruta o nombre problemático, cópialo a una carpeta corta y renómbralo
          antes de reintentar.
        </StatusAlert>
      ))}
      <small className="hint">
        Límite de la sesión: 100 MB por MSG. Los adjuntos mayores de 10 MB se señalan, pero se intentan
        procesar.
      </small>
    </div>
  )
}
