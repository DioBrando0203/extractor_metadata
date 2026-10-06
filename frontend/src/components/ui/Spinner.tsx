type Props = { size?: 'sm' | 'md' | 'lg'; label?: string; tone?: 'brand' | 'inverted' }

/** Indicador de progreso circular. Con `label` se anuncia; sin él es decorativo. */
export function Spinner({ size = 'md', label, tone = 'brand' }: Props) {
  return (
    <span
      className={`spinner spinner--${size} spinner--${tone}`}
      role={label ? 'status' : undefined}
      aria-hidden={label ? undefined : true}
    >
      {label && <span className="sr-only">{label}</span>}
    </span>
  )
}
