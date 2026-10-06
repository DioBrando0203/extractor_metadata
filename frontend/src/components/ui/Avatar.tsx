import { UserRound } from 'lucide-react'

type Props = { name?: string | null; size?: 'sm' | 'md' }

const TONES = 6

/** Iniciales de un nombre o, si es una dirección, de su parte local. */
function initials(name: string): string {
  const base = name.includes('@') && !name.trim().includes(' ') ? name.split('@')[0] : name
  const words = base
    .replace(/[^\p{L}\p{N}\s._-]/gu, ' ')
    .split(/[\s._-]+/)
    .filter(Boolean)
  if (!words.length) return ''
  const last = words.length > 1 ? words[words.length - 1][0] : ''
  return `${words[0][0]}${last}`.toUpperCase()
}

/** Tono estable por nombre: la misma persona conserva su color en toda la sesión. */
function tone(name: string): number {
  let hash = 0
  for (const char of name.toLowerCase()) hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  return (hash % TONES) + 1
}

/** Avatar decorativo: el nombre siempre se muestra como texto junto a él. */
export function Avatar({ name, size = 'md' }: Props) {
  const label = name?.trim() ? initials(name) : ''
  if (!label) {
    return (
      <span className={`avatar avatar--${size} avatar--empty`} aria-hidden="true">
        <UserRound size={size === 'sm' ? 16 : 20} />
      </span>
    )
  }
  return (
    <span className={`avatar avatar--${size}`} data-tone={tone(name ?? '')} aria-hidden="true">
      {label}
    </span>
  )
}
