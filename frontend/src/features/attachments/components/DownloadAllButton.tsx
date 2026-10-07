import { useState } from 'react'
import { FolderZip16Regular } from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import { Spinner } from '../../../components/ui/Spinner'

type Props = { onDownloadAll: () => Promise<void> }

/** "Descargar todo": un ZIP con los adjuntos que traen bytes (los enlaces no viajan en el correo). */
export function DownloadAllButton({ onDownloadAll }: Props) {
  const [state, setState] = useState<'idle' | 'busy' | 'error'>('idle')

  async function download() {
    setState('busy')
    try {
      await onDownloadAll()
      setState('idle')
    } catch {
      setState('error')
    }
  }

  return (
    <>
      <Button
        variant="subtle"
        size="sm"
        onClick={() => void download()}
        disabled={state === 'busy'}
        aria-busy={state === 'busy' || undefined}
      >
        {state === 'busy' ? <Spinner size="sm" /> : <FolderZip16Regular aria-hidden="true" />} Descargar todo
      </Button>
      {state === 'error' && (
        <p className="attachments__zip-error" role="alert">
          No se pudieron preparar los adjuntos. Inténtalo otra vez.
        </p>
      )}
    </>
  )
}
