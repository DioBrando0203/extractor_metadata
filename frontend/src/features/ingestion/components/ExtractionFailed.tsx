import { ArrowClockwise20Regular, ErrorCircle24Regular, FolderOpen20Regular } from '@fluentui/react-icons'
import { Button } from '../../../components/ui/Button'
import { EmptyState } from '../../../components/ui/EmptyState'
import { StatusAlert } from '../../../components/ui/StatusAlert'

type Props = {
  name: string
  error?: string
  retryable: boolean
  onRetry: () => void
  onBrowse: () => void
}

export function ExtractionFailed({ name, error, retryable, onRetry, onBrowse }: Props) {
  return (
    <EmptyState
      tone="danger"
      icon={<ErrorCircle24Regular />}
      title={`No se pudo abrir “${name}”`}
      actions={
        <>
          {retryable && (
            <Button onClick={onRetry}>
              <ArrowClockwise20Regular aria-hidden="true" /> Reintentar
            </Button>
          )}
          <Button variant={retryable ? 'secondary' : 'primary'} onClick={onBrowse}>
            <FolderOpen20Regular aria-hidden="true" /> Abrir otro archivo
          </Button>
        </>
      }
    >
      <StatusAlert tone="error">{error || 'No fue posible leer el archivo.'}</StatusAlert>
      {retryable && (
        <p>
          Los demás archivos de la bandeja siguen procesándose. Si el error menciona la ruta o el nombre,
          copia el archivo a una carpeta corta y renómbralo antes de reintentar.
        </p>
      )}
    </EmptyState>
  )
}
