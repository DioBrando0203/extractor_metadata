import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  /** Apariencias de Fluent 2: primary (una por zona), secondary, subtle (barras de comandos), danger. */
  variant?: 'primary' | 'secondary' | 'subtle' | 'danger'
  size?: 'md' | 'sm'
  /** Botón cuadrado sólo con icono; exige `aria-label`. */
  iconOnly?: boolean
}

export function Button({
  children,
  className = '',
  variant = 'primary',
  size = 'md',
  iconOnly = false,
  type = 'button',
  ...props
}: Props) {
  const classes = ['button', `button--${variant}`, `button--${size}`, iconOnly && 'button--icon', className]
  return (
    <button type={type} className={classes.filter(Boolean).join(' ')} {...props}>
      {children}
    </button>
  )
}
