import { useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { CircleAlert, FilePlus2, HelpCircle, RotateCcw } from 'lucide-react'
import { AppLayout } from '../components/layout/AppLayout'
import { Button } from '../components/ui/Button'
import { StatusAlert } from '../components/ui/StatusAlert'
import { Dropzone } from '../features/ingestion/components/Dropzone'
import { QueueList } from '../features/ingestion/components/QueueList'
import { useExtractionQueue } from '../features/ingestion/hooks/useExtractionQueue'
import { MessageViewer } from '../features/message-viewer/components/MessageViewer'
import { fileValidationError } from '../features/ingestion/lib/validation'

function Help() {
  return (
    <div className="help-page">
      <span className="eyebrow">
        <HelpCircle size={16} /> Guía rápida
      </span>
      <h1>Cómo analizar un MSG</h1>
      <ol>
        <li>
          Arrastra uno o varios archivos con extensión <b>.msg</b> o selecciónalos desde tu equipo.
        </li>
        <li>La bandeja los procesa en orden para que un error no bloquee los demás.</li>
        <li>Selecciona cualquier resultado para leer el correo y descargar sus archivos.</li>
        <li>
          Si falla, usa <b>Reintentar</b>. Para errores de ruta o nombre, copia el archivo a una carpeta corta
          y renómbralo.
        </li>
      </ol>
      <StatusAlert tone="info" title="Privacidad">
        Esta interfaz no crea cuentas ni conserva archivos al recargar. El backend local procesa el archivo
        que seleccionaste.
      </StatusAlert>
      <h2>Qué significa “parcial”</h2>
      <p>
        Se recuperó una parte del correo. Aun así puedes leer lo disponible y descargar los archivos que
        aparezcan en Adjuntos.
      </p>
    </div>
  )
}

function FailedMessage({
  name,
  error,
  onRetry,
  onChoose,
  retryable,
}: {
  name: string
  error?: string
  onRetry: () => void
  onChoose: () => void
  retryable: boolean
}) {
  return (
    <div className="failed-reader">
      <CircleAlert size={38} />
      <h1>No se pudo analizar “{name}”</h1>
      <StatusAlert tone="error" title="Error de extracción">
        {error || 'No fue posible leer el archivo.'}
      </StatusAlert>
      <p>
        El resto de archivos en la cola seguirá procesándose.
        {retryable
          ? ' Puedes reintentar este archivo sin volver a cargarlo.'
          : ' Selecciona un MSG para continuar.'}
      </p>
      <div className="action-row">
        <Button onClick={onRetry} disabled={!retryable}>
          <RotateCcw size={16} /> Reintentar
        </Button>
        <Button variant="secondary" onClick={onChoose}>
          <FilePlus2 size={16} /> Agregar archivos
        </Button>
      </div>
    </div>
  )
}
function ProcessingMessage({ name, extracting }: { name: string; extracting: boolean }) {
  return (
    <div className="selection-prompt">
      <FilePlus2 className={extracting ? 'spin' : ''} size={34} />
      <h1>{extracting ? 'Leyendo el correo' : 'En espera de análisis'}</h1>
      <p>
        “{name}”{' '}
        {extracting ? 'se está procesando.' : 'se procesará cuando terminen los archivos anteriores.'}
      </p>
    </div>
  )
}

export function App() {
  const { items, selectedId, setSelectedId, addFiles, retry, clear } = useExtractionQueue()
  const [activeView, setActiveView] = useState<'analysis' | 'help'>('analysis')
  const input = useRef<HTMLInputElement>(null)
  const selected = items.find((item) => item.id === selectedId)
  const errors = items
    .filter((item) => item.status === 'error')
    .map((item) => `${item.file.name}: ${item.error || 'Error de extracción.'}`)
  const choose = () => input.current?.click()
  const onInput = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files?.length) addFiles(Array.from(event.target.files))
    event.target.value = ''
  }
  const sidebar = (
    <QueueList
      items={items}
      selectedId={selectedId}
      onSelect={(id) => {
        setSelectedId(id)
        setActiveView('analysis')
      }}
      onRetry={retry}
      onClear={clear}
    />
  )

  return (
    <AppLayout activeView={activeView} onViewChange={setActiveView} sidebar={sidebar}>
      <input
        ref={input}
        type="file"
        accept=".msg,application/vnd.ms-outlook"
        multiple
        hidden
        onChange={onInput}
      />
      {activeView === 'help' ? (
        <Help />
      ) : !items.length ? (
        <Dropzone busy={false} errors={errors} onFiles={addFiles} />
      ) : selected?.message ? (
        <MessageViewer message={selected.message} file={selected.file} onChoose={choose} />
      ) : selected?.status === 'error' ? (
        <FailedMessage
          name={selected.file.name}
          error={selected.error}
          onRetry={() => retry(selected.id)}
          onChoose={choose}
          retryable={!fileValidationError(selected.file)}
        />
      ) : selected ? (
        <ProcessingMessage name={selected.file.name} extracting={selected.status === 'extracting'} />
      ) : (
        <div className="selection-prompt">
          <FilePlus2 size={34} />
          <h1>Selecciona un mensaje de la bandeja</h1>
          <p>O agrega más archivos MSG a la cola.</p>
          <Button onClick={choose}>Agregar archivos</Button>
        </div>
      )}
    </AppLayout>
  )
}
