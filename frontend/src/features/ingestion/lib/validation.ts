export function fileValidationError(file: File): string | undefined {
  if (!file.name.toLowerCase().endsWith('.msg')) return 'Selecciona archivos con extensión .msg.'
  return undefined
}
