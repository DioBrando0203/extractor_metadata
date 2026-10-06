import { createContext, useContext } from 'react'

/** Términos de búsqueda activos para resaltar dentro del correo abierto (vacío si no se busca). */
export const HighlightContext = createContext<string[]>([])

export function useHighlightTerms(): string[] {
  return useContext(HighlightContext)
}
