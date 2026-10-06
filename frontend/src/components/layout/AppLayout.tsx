import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import { ChevronLeft, CircleHelp, Inbox, MailSearch, ShieldCheck } from 'lucide-react'
import { Button } from '../ui/Button'

export type View = 'analysis' | 'help'
export type Pane = 'list' | 'reader'

type Props = {
  children: ReactNode
  activeView: View
  onViewChange: (view: View) => void
  /** Panel de lista. Si falta, el lector ocupa todo el ancho disponible. */
  list?: ReactNode
  /** Panel visible en pantallas angostas, donde lista y lector no caben juntos. */
  pane: Pane
  /** Acción "volver a la lista" que sólo se muestra en pantallas angostas. */
  back?: { label: string; onClick: () => void }
  /** Cambia cuando el contenido del lector es otro; devuelve el scroll al inicio. */
  contentKey?: string
  overlay?: ReactNode
}

const NAVIGATION: { view: View; label: string; icon: typeof Inbox }[] = [
  { view: 'analysis', label: 'Bandeja', icon: Inbox },
  { view: 'help', label: 'Ayuda', icon: CircleHelp },
]

export function AppLayout({
  children,
  activeView,
  onViewChange,
  list,
  pane,
  back,
  contentKey,
  overlay,
}: Props) {
  const reader = useRef<HTMLElement>(null)

  useEffect(() => {
    if (reader.current) reader.current.scrollTop = 0
  }, [contentKey])

  return (
    <div className="app-shell">
      <a className="skip-link" href="#reader">
        Saltar al contenido
      </a>
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true">
            <MailSearch size={18} />
          </span>
          <span className="brand__name">
            Inspector <strong>MSG</strong>
          </span>
        </div>
        <p className="topbar__badge" title="Sin cuenta, sin nube y sin historial">
          <ShieldCheck size={15} aria-hidden="true" />
          <span className="topbar__badge-text">Sesión local · sin cuenta</span>
        </p>
      </header>
      <div className={`workspace ${list ? 'workspace--with-list' : ''}`} data-pane={pane}>
        <nav className="rail" aria-label="Navegación principal">
          {NAVIGATION.map(({ view, label, icon: Icon }) => (
            <button
              key={view}
              type="button"
              className="rail__item"
              aria-current={activeView === view ? 'page' : undefined}
              onClick={() => onViewChange(view)}
            >
              <Icon size={20} aria-hidden="true" />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        {list}
        <main id="reader" ref={reader} className="reader" tabIndex={-1}>
          {back && (
            <div className="reader__back">
              <Button variant="ghost" size="sm" onClick={back.onClick}>
                <ChevronLeft size={16} aria-hidden="true" /> {back.label}
              </Button>
            </div>
          )}
          {children}
        </main>
      </div>
      {overlay}
    </div>
  )
}
