import type { ReactNode } from 'react'
import { FileSearch, HelpCircle, Inbox, ShieldCheck } from 'lucide-react'
import { Button } from '../ui/Button'
type Props = {
  children: ReactNode
  activeView: 'analysis' | 'help'
  onViewChange: (view: 'analysis' | 'help') => void
  sidebar: ReactNode
}
export function AppLayout({ children, activeView, onViewChange, sidebar }: Props) {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">
            <FileSearch size={20} />
          </span>
          <span>
            Inspector <b>MSG</b>
          </span>
        </div>
        <div className="local-badge">
          <ShieldCheck size={16} /> Sesión local · sin cuenta
        </div>
      </header>
      <div className="workspace">
        <nav className="rail" aria-label="Navegación principal">
          <Button
            variant="ghost"
            className={`rail-item ${activeView === 'analysis' ? 'is-active' : ''}`}
            aria-current={activeView === 'analysis' ? 'page' : undefined}
            onClick={() => onViewChange('analysis')}
          >
            <Inbox size={20} />
            <span>Análisis</span>
          </Button>
          <Button
            variant="ghost"
            className={`rail-item ${activeView === 'help' ? 'is-active' : ''}`}
            aria-current={activeView === 'help' ? 'page' : undefined}
            onClick={() => onViewChange('help')}
          >
            <HelpCircle size={20} />
            <span>Ayuda</span>
          </Button>
        </nav>
        {sidebar}
        <section className="reader" aria-live="polite">
          {children}
        </section>
      </div>
      <footer>Los archivos y resultados permanecen sólo en la memoria de esta sesión.</footer>
    </main>
  )
}
