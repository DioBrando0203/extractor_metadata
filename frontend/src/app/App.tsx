import { useCallback, useRef, useState } from 'react'
import type { ChangeEvent, ReactNode } from 'react'
import { FolderOpen, MailOpen } from 'lucide-react'
import { AppLayout } from '../components/layout/AppLayout'
import type { Pane, View } from '../components/layout/AppLayout'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { HelpPage } from '../features/help/components/HelpPage'
import { DropOverlay } from '../features/ingestion/components/DropOverlay'
import { Dropzone } from '../features/ingestion/components/Dropzone'
import { ExtractionFailed } from '../features/ingestion/components/ExtractionFailed'
import { QueueList } from '../features/ingestion/components/QueueList'
import { useExtractionQueue } from '../features/ingestion/hooks/useExtractionQueue'
import { useWindowFileDrop } from '../features/ingestion/hooks/useWindowFileDrop'
import { fileValidationError } from '../features/ingestion/lib/validation'
import { MessageLoading } from '../features/message-viewer/components/MessageLoading'
import { MessageViewer } from '../features/message-viewer/components/MessageViewer'

const MSG_ACCEPT = '.msg,application/vnd.ms-outlook'

export function App() {
  const { items, selectedId, setSelectedId, addFiles, retry, clear } = useExtractionQueue()
  const [activeView, setActiveView] = useState<View>('analysis')
  const [pane, setPane] = useState<Pane>('reader')
  const input = useRef<HTMLInputElement>(null)
  const selected = items.find((item) => item.id === selectedId)
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

  let content: ReactNode
  if (activeView === 'help') {
    content = <HelpPage />
  } else if (!hasItems) {
    content = <Dropzone active={dragging} onBrowse={browse} />
  } else if (selected?.message) {
    content = <MessageViewer key={selected.id} message={selected.message} file={selected.file} />
  } else if (selected?.status === 'error') {
    content = (
      <ExtractionFailed
        name={selected.file.name}
        error={selected.error}
        retryable={!fileValidationError(selected.file)}
        onRetry={() => retry(selected.id)}
        onBrowse={browse}
      />
    )
  } else if (selected) {
    content = <MessageLoading name={selected.file.name} waiting={selected.status === 'queued'} />
  } else {
    content = (
      <EmptyState
        icon={<MailOpen size={26} />}
        title="Selecciona un correo para leerlo"
        actions={
          <Button variant="secondary" onClick={browse}>
            <FolderOpen size={16} aria-hidden="true" /> Abrir MSG
          </Button>
        }
      >
        <p>Elige un elemento de la bandeja o abre más archivos .msg.</p>
      </EmptyState>
    )
  }

  const showReader = activeView === 'help' || !hasItems || pane === 'reader'

  return (
    <>
      <input ref={input} type="file" accept={MSG_ACCEPT} multiple hidden onChange={onInput} />
      <AppLayout
        activeView={activeView}
        onViewChange={changeView}
        pane={showReader ? 'reader' : 'list'}
        contentKey={`${activeView}:${selectedId ?? ''}`}
        back={
          activeView === 'analysis' && hasItems
            ? { label: `Bandeja (${items.length})`, onClick: () => setPane('list') }
            : undefined
        }
        list={
          hasItems ? (
            <QueueList
              items={items}
              selectedId={selectedId}
              onSelect={select}
              onRetry={retry}
              onClear={clear}
              onAdd={browse}
            />
          ) : undefined
        }
        overlay={dragging && hasItems ? <DropOverlay /> : null}
      >
        {content}
      </AppLayout>
    </>
  )
}
