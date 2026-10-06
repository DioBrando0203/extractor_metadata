/**
 * Decodifica texto de un adjunto: UTF-8 si es válido; si no, Windows-1252, habitual en archivos
 * generados en Windows en español.
 */
export function decodeText(buffer: ArrayBuffer): string {
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(buffer)
  } catch {
    return new TextDecoder('windows-1252').decode(buffer)
  }
}
