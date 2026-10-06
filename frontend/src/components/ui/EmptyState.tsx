import type { ReactNode } from 'react'

type Props = {
  icon: ReactNode
  title: string
  tone?: 'brand' | 'danger'
  children?: ReactNode
  actions?: ReactNode
}

/** Tarjeta centrada para estados sin contenido principal: vacío, error o selección pendiente. */
export function EmptyState({ icon, title, tone = 'brand', children, actions }: Props) {
  return (
    <section className={`empty-state empty-state--${tone}`}>
      <span className="empty-state__icon" aria-hidden="true">
        {icon}
      </span>
      <h1 className="empty-state__title">{title}</h1>
      {children && <div className="empty-state__text">{children}</div>}
      {actions && <div className="empty-state__actions">{actions}</div>}
    </section>
  )
}
