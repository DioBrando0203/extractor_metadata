import { useCallback, useMemo, useRef, useState } from 'react'
import type { ChangeEvent, ReactNode } from 'react'
import { Add20Regular, Delete20Regular, FolderOpen20Regular, MailRead24Regular } from '@fluentui/react-icons'
import { AppLayout } from '../components/layout/AppLayout'
import type { Pane, View } from '../components/layout/AppLayout'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { SearchBox } from '../components/ui/SearchBox'
import { HelpPage } from '../features/help/components/HelpPage'
import { DropOverlay } from '../features/ingestion/components/DropOverlay'
import { Dropzone } from '../features/ingestion/components/Dropzone'
import { ExtractionFailed } from '../features/ingestion/components/ExtractionFailed'
import { QueueList } from '../features/ingestion/components/QueueList'
import { useExtractionQueue } from '../features/ingestion/hooks/useExtractionQueue'
import { useWindowFileDrop } from '../features/ingestion/hooks/useWindowFileDrop'
import { filterQueue } from '../features/ingestion/lib/search'
import { fileValidationError } from '../features/ingestion/lib/validation'
import { MessageLoading } from '../features/message-viewer/components/MessageLoading'
import { MessageViewer } from '../features/message-viewer/components/MessageViewer'
import type { QueueItem } from '../lib/types'

const MSG_ACCEPT = '.msg,application/vnd.ms-outlook'

export function App() {
  const { items, selectedId, setSelectedId, addFiles, retry, clear } = useExtractionQueue()
  const [activeView, setActiveView] = useState<View>('analysis')
  const [pane, setPane] = useState<Pane>('reader')
  const [query, setQuery] = useState('')
  const input = useRef<HTMLInputElement>(null)
  const selected = items.find((item) => item.id === selectedId)
  const visibleItems = useMemo(() => filterQueue(items, query), [items, query])
  const hasItems = items.length > 0

  const browse = () => input.current?.click()

  const add = useCallback(
    (files: File[]) => {
      if (!files.length) return
      addFiles(files)
      setActiveView('analysis')
      // Si ya se estaba leyendo un correo, en móvil se muestra la bandeja con los nuevos archivos.
      setPane(selectedId ? 'list' : 'reader')
    },
    [addFiles, selectedId],
  )
  const dragging = useWindowFileDrop(add)

  const onInput = (event: ChangeEvent<HTMLInputElement>) => {
    add(Array.from(event.target.files ?? []))
    event.target.value = ''
  }
  const select = (id: string) => {
    setSelectedId(id)
    setActiveView('analysis')
    setPane('reader')
  }
  const changeView = (view: View) => {
    setActiveView(view)
    setPane(view === 'analysis' ? 'list' : 'reader')
  }
  const clearSession = () => {
    clear()
    setQuery('')
  }

  const commands = hasItems ? (
    <>
      <Button onClick={browse}>
        <Add20Regular aria-hidden="true" /> Abrir MSG
      </Button>
      <span className="command-bar__divider" aria-hidden="true" />
      <Button variant="subtle" onClick={clearSession}>
        <Delete20Regular aria-hidden="true" /> Limpiar bandeja
      </Button>
    </>
  ) : undefined

  return (
    <>
      <input ref={input} type="file" accept={MSG_ACCEPT} multiple hidden onChange={onInput} />
      <AppLayout
        activeView={activeView}
        onViewChange={changeView}
        pane={activeView === 'help' || !hasItems || pane === 'reader' ? 'reader' : 'list'}
        contentKey={`${activeView}:${selectedId ?? ''}`}
        search={
          hasItems ? (
            <SearchBox
              value={query}
              onChange={(value) => {
                setQuery(value)
                if (value) changeView('analysis')
              }}
              placeholder="Buscar en la bandeja"
              label="Buscar por asunto, remitente, texto o adjunto"
            />
          ) : undefined
        }
        commands={commands}
        back={
          activeView === 'analysis' && hasItems
            ? { label: `Bandeja (${items.length})`, onClick: () => setPane('list') }
            : undefined
        }
        list={
          hasItems ? (
            <QueueList
              items={visibleItems}
              total={items.length}
              query={query}
              selectedId={selectedId}
              onSelect={select}
              onRetry={retry}
              onClearQuery={() => setQuery('')}
            />
          ) : undefined
        }
        overlay={dragging && hasItems ? <DropOverlay /> : null}
      >
        <ReaderContent
          view={activeView}
          hasItems={hasItems}
          selected={selected}
          dragging={dragging}
          onBrowse={browse}
          onRetry={retry}
        />
      </AppLayout>
    </>
  )
}

type ReaderProps = {
  view: View
  hasItems: boolean
  selected?: QueueItem
  dragging: boolean
  onBrowse: () => void
  onRetry: (id: string) => void
}

/** Decide qué muestra el lector según la vista y el estado del correo seleccionado (SPEC-01). */
function ReaderContent({ view, hasItems, selected, dragging, onBrowse, onRetry }: ReaderProps): ReactNode {
  if (view === 'help') return <HelpPage />
  if (!hasItems) return <Dropzone active={dragging} onBrowse={onBrowse} />
  if (selected?.message)
    return <MessageViewer key={selected.id} message={selected.message} file={selected.file} />
  if (selected?.status === 'error') {
    return (
      <ExtractionFailed
        name={selected.file.name}
        error={selected.error}
        retryable={!fileValidationError(selected.file)}
        onRetry={() => onRetry(selected.id)}
        onBrowse={onBrowse}
      />
    )
  }
  if (selected) return <MessageLoading name={selected.file.name} waiting={selected.status === 'queued'} />
  return (
    <EmptyState
      icon={<MailRead24Regular />}
      title="Selecciona un correo para leerlo"
      actions={
        <Button variant="secondary" onClick={onBrowse}>
          <FolderOpen20Regular aria-hidden="true" /> Abrir MSG
        </Button>
      }
    >
      <p>Elige un elemento de la bandeja o abre más archivos .msg.</p>
    </EmptyState>
  )
}
