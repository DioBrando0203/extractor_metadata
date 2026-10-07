import { useCallback, useEffect, useMemo, useRef } from 'react'
import { fetchAttachment, saveBlob } from '../../../lib/api'
import type { Attachment, AttachmentFile } from '../../../lib/types'

export type Variant = 'original' | 'preview'
export type AttachmentFiles = ReturnType<typeof useAttachmentFiles>

/** Sin correos adjuntos de por medio: el adjunto está en el correo principal. */
const ROOT: readonly number[] = []

/**
 * Caché en memoria de los binarios pedidos mientras se lee un correo. Evita reenviar el MSG al volver a
 * ver o descargar el mismo adjunto y revoca todas las URLs `blob:` al desmontar el lector.
 * `messagePath` ubica el correo adjunto que se está leyendo dentro del archivo.
 */
export function useAttachmentFiles(file: File, messagePath: readonly number[] = ROOT) {
  const files = useRef(new Map<string, Promise<AttachmentFile>>())
  const urls = useRef(new Map<string, string>())

  useEffect(() => {
    const fileCache = files.current
    const urlCache = urls.current
    return () => {
      urlCache.forEach((url) => URL.revokeObjectURL(url))
      urlCache.clear()
      fileCache.clear()
    }
  }, [])

  const load = useCallback(
    (attachment: Attachment, index: number, variant: Variant = 'original') => {
      const key = `${index}:${variant}`
      const cached = files.current.get(key)
      if (cached) return cached
      const pending = fetchAttachment(file, index, attachment.name, {
        preview: variant === 'preview',
        messagePath,
      })
      // Un fallo no queda en caché: el usuario puede reintentar.
      pending.catch(() => files.current.delete(key))
      files.current.set(key, pending)
      return pending
    },
    [file, messagePath],
  )

  /** URL `blob:` estable para un adjunto, con el tipo MIME que necesita el visor. */
  const objectUrl = useCallback(
    async (attachment: Attachment, index: number, variant: Variant, type?: string) => {
      const key = `${index}:${variant}:${type ?? ''}`
      const existing = urls.current.get(key)
      if (existing) return existing
      const { blob } = await load(attachment, index, variant)
      const url = URL.createObjectURL(!type || blob.type === type ? blob : new Blob([blob], { type }))
      urls.current.set(key, url)
      return url
    },
    [load],
  )

  const download = useCallback(
    async (attachment: Attachment, index: number) => {
      const loaded = await load(attachment, index)
      saveBlob(loaded.blob, loaded.filename)
    },
    [load],
  )

  return useMemo(() => ({ load, objectUrl, download }), [load, objectUrl, download])
}
