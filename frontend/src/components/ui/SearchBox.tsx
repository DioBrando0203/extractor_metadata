import { useEffect, useRef } from 'react'
import { Dismiss16Regular, Search20Regular } from '@fluentui/react-icons'

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
  /** Tecla que enfoca el buscador desde cualquier parte, salvo mientras se escribe en otro campo. */
  shortcut?: string
}

function isTyping(target: EventTarget | null): boolean {
  return (
    target instanceof HTMLElement &&
    (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
  )
}

/** Campo de búsqueda con icono, botón para borrar y atajo de teclado; Esc también lo vacía. */
export function SearchBox({ value, onChange, placeholder, label, shortcut }: Props) {
  const input = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!shortcut) return
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== shortcut || event.ctrlKey || event.metaKey || event.altKey) return
      if (isTyping(event.target)) return
      event.preventDefault()
      input.current?.focus()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [shortcut])

  return (
    <div className="search-box" role="search">
      <Search20Regular className="search-box__icon" aria-hidden="true" />
      <input
        ref={input}
        type="search"
        value={value}
        placeholder={placeholder}
        aria-label={label}
        aria-keyshortcuts={shortcut}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && value) {
            event.preventDefault()
            onChange('')
          }
        }}
      />
      {value ? (
        <button
          type="button"
          className="search-box__clear"
          aria-label="Borrar búsqueda"
          onClick={() => onChange('')}
        >
          <Dismiss16Regular aria-hidden="true" />
        </button>
      ) : (
        shortcut && (
          <kbd className="search-box__shortcut" aria-hidden="true">
            {shortcut}
          </kbd>
        )
      )}
    </div>
  )
}
