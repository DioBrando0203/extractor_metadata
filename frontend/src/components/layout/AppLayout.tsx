import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import {
  ChevronLeft20Regular,
  MailInbox24Filled,
  MailInbox24Regular,
  QuestionCircle24Filled,
  QuestionCircle24Regular,
  ShieldCheckmark16Regular,
} from '@fluentui/react-icons'
import type { FluentIcon } from '@fluentui/react-icons'
import { Button } from '../ui/Button'

export type View = 'analysis' | 'help'
export type Pane = 'list' | 'reader'
export type NavigationItem = { id: string; label: string; icon: FluentIcon; activeIcon: FluentIcon }

type Props = {
  children: ReactNode
  activeView: View
  onViewChange: (view: View) => void
  navigation?: NavigationItem[]
  activeNavigation?: string
  onNavigationChange?: (id: string) => void
  onBrandClick?: () => void
  /** Buscador de la cabecera; sólo tiene sentido cuando hay correos. */
  search?: ReactNode
  /** Barra de comandos sobre la bandeja y el lector. */
  commands?: ReactNode
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

const NAVIGATION: NavigationItem[] = [
  { id: 'analysis', label: 'Correo', icon: MailInbox24Regular, activeIcon: MailInbox24Filled },
  { id: 'help', label: 'Ayuda', icon: QuestionCircle24Regular, activeIcon: QuestionCircle24Filled },
]

export function AppLayout({
  children,
  activeView,
  onViewChange,
  navigation,
  activeNavigation,
  onNavigationChange,
  onBrandClick,
  search,
  commands,
  list,
  pane,
  back,
  contentKey,
  overlay,
}: Props) {
  const reader = useRef<HTMLElement>(null)
  const items = navigation ?? NAVIGATION
  const selected = activeNavigation ?? activeView
  const changeNavigation = onNavigationChange ?? ((id: string) => onViewChange(id as View))

  useEffect(() => {
    if (reader.current) reader.current.scrollTop = 0
  }, [contentKey])

  return (
    <div className="app-shell">
      <a className="skip-link" href="#reader">
        Saltar al contenido
      </a>
      <header className="app-header">
        <button className="brand" type="button" onClick={onBrandClick} aria-label="Herramientas">
          <span className="brand__mark" aria-hidden="true">
            <MailInbox24Filled />
          </span>
          <span className="brand__name">Inspector MSG</span>
        </button>
        <div className="app-header__search">{search}</div>
        <p className="app-header__badge" title="Sin cuenta, sin nube y sin historial">
          <ShieldCheckmark16Regular aria-hidden="true" />
          <span className="app-header__badge-text">Sesión local</span>
        </p>
      </header>
      <div className="app-body">
        <nav className="app-bar" aria-label="Navegación principal">
          {items.map(({ id, label, icon: Icon, activeIcon: ActiveIcon }) => {
            const active = selected === id
            return (
              <button
                key={id}
                type="button"
                className="app-bar__item"
                aria-current={active ? 'page' : undefined}
                onClick={() => changeNavigation(id)}
              >
                {active ? <ActiveIcon aria-hidden="true" /> : <Icon aria-hidden="true" />}
                <span>{label}</span>
              </button>
            )
          })}
        </nav>
        <div
          className={['workspace', list && 'workspace--with-list', commands && 'workspace--with-commands']
            .filter(Boolean)
            .join(' ')}
          data-pane={pane}
        >
          {commands && (
            <div className="command-bar" role="toolbar" aria-label="Acciones de la bandeja">
              {commands}
            </div>
          )}
          {list}
          <main id="reader" ref={reader} className="reader" tabIndex={-1}>
            {back && (
              <div className="reader__back">
                <Button variant="subtle" size="sm" onClick={back.onClick}>
                  <ChevronLeft20Regular aria-hidden="true" /> {back.label}
                </Button>
              </div>
            )}
            {children}
          </main>
        </div>
      </div>
      {overlay}
    </div>
  )
}
