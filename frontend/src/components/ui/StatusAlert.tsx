import type { ReactNode } from 'react'
import { CircleAlert, CircleCheck, Info, TriangleAlert } from 'lucide-react'
type Props = { tone: 'error' | 'warning' | 'success' | 'info'; children: ReactNode; title?: string }
const icons = { error: CircleAlert, warning: TriangleAlert, success: CircleCheck, info: Info }
export function StatusAlert({ tone, title, children }: Props) {
  const Icon = icons[tone]
  return (
    <div className={`status-alert status-alert--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>
      <Icon aria-hidden="true" size={19} />
      <div>
        {title && <strong>{title}</strong>}
        <div>{children}</div>
      </div>
    </div>
  )
}
