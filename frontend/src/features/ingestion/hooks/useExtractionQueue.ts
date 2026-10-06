import { useCallback, useRef, useState } from 'react'
import { extractMessage } from '../../../lib/api'
import type { QueueItem } from '../../../lib/types'
import { fileValidationError } from '../lib/validation'

const makeId = () =>
  typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`

export function useExtractionQueue() {
  const [items, setItems] = useState<QueueItem[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const itemsRef = useRef<QueueItem[]>([])
  const pendingRef = useRef<string[]>([])
  const runningRef = useRef(false)

  const replaceItems = useCallback((updater: (current: QueueItem[]) => QueueItem[]) => {
    const next = updater(itemsRef.current)
    itemsRef.current = next
    setItems(next)
  }, [])

  const process = useCallback(async () => {
    if (runningRef.current) return
    runningRef.current = true
    while (pendingRef.current.length) {
      const id = pendingRef.current.shift()
      const task = itemsRef.current.find((item) => item.id === id)
      if (!id || !task) continue
      replaceItems((current) =>
        current.map((item) => (item.id === id ? { ...item, status: 'extracting', error: undefined } : item)),
      )
      try {
        const result = await extractMessage(task.file)
        replaceItems((current) =>
          current.map((item) =>
            item.id === id ? { ...item, status: result.message.status, message: result.message } : item,
          ),
        )
        if (itemsRef.current.some((item) => item.id === id)) {
          setSelectedId((current) => current ?? id)
        }
      } catch (reason) {
        const error = reason instanceof Error ? reason.message : 'Error desconocido al extraer el mensaje.'
        replaceItems((current) =>
          current.map((item) => (item.id === id ? { ...item, status: 'error', error } : item)),
        )
        if (itemsRef.current.some((item) => item.id === id)) {
          setSelectedId((current) => current ?? id)
        }
      }
    }
    runningRef.current = false
  }, [replaceItems])

  const addFiles = useCallback(
    (files: File[]) => {
      const additions: QueueItem[] = files.map((file) => {
        const error = fileValidationError(file)
        return { id: makeId(), file, status: error ? 'error' : 'queued', error }
      })
      replaceItems((current) => [...current, ...additions])
      const valid = additions.filter((item) => item.status === 'queued')
      if (valid.length) {
        pendingRef.current.push(...valid.map((item) => item.id))
        void process()
      }
      if (!selectedId && additions.length) setSelectedId(additions[0].id)
    },
    [process, replaceItems, selectedId],
  )

  const retry = useCallback(
    (id: string) => {
      const task = itemsRef.current.find((item) => item.id === id)
      if (!task || task.status === 'extracting' || task.status === 'queued' || fileValidationError(task.file))
        return
      replaceItems((current) =>
        current.map((item) => (item.id === id ? { ...item, status: 'queued', error: undefined } : item)),
      )
      pendingRef.current.push(id)
      void process()
    },
    [process, replaceItems],
  )

  const clear = useCallback(() => {
    pendingRef.current = []
    replaceItems(() => [])
    setSelectedId(null)
  }, [replaceItems])

  return { items, selectedId, setSelectedId, addFiles, retry, clear }
}
