import { Dismiss16Regular, Search20Regular } from '@fluentui/react-icons'

type Props = {
  value: string
  onChange: (value: string) => void
  placeholder: string
  label: string
}

/** Campo de búsqueda con icono y botón para borrar; Esc también lo vacía. */
export function SearchBox({ value, onChange, placeholder, label }: Props) {
  return (
    <div className="search-box" role="search">
      <Search20Regular className="search-box__icon" aria-hidden="true" />
      <input
        type="search"
        value={value}
        placeholder={placeholder}
        aria-label={label}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && value) {
            event.preventDefault()
            onChange('')
          }
        }}
      />
      {value && (
        <button
          type="button"
          className="search-box__clear"
          aria-label="Borrar búsqueda"
          onClick={() => onChange('')}
        >
          <Dismiss16Regular aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
