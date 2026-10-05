export const MAX_MSG_BYTES = 100 * 1024 * 1024

export function fileValidationError(file: File): string | undefined {
  if (!file.name.toLowerCase().endsWith('.msg')) return 'Selecciona archivos con extensión .msg.'
  if (file.size > MAX_MSG_BYTES) return 'El MSG supera el límite local de 100 MB.'
  return undefined
}
