import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { ExtractionResponse } from '../../../lib/types'

const mocks = vi.hoisted(() => ({ extractMessage: vi.fn() }))
vi.mock('../../../lib/api', () => ({ extractMessage: mocks.extractMessage }))
import { useExtractionQueue } from './useExtractionQueue'

const response = (name: string): ExtractionResponse => ({
  processed_locally: true,
  message: {
    file_name: name,
    file_size_bytes: 1,
    subject: name,
    recipients: [],
    body_truncated: false,
    headers: [],
    properties: [],
    attachments: [],
    warnings: [],
    status: 'complete',
  },
})

describe('useExtractionQueue', () => {
  it('continúa con el segundo MSG después de un error y permite reintentar el primero', async () => {
    mocks.extractMessage
      .mockRejectedValueOnce(new Error('Archivo corrupto'))
      .mockResolvedValueOnce(response('segundo.msg'))
      .mockResolvedValueOnce(response('primero.msg'))
    const { result } = renderHook(() => useExtractionQueue())
    const first = new File(['a'], 'primero.msg')
    const second = new File(['b'], 'segundo.msg')
    act(() => result.current.addFiles([first, second]))

    await waitFor(() =>
      expect(result.current.items.map((item) => item.status)).toEqual(['error', 'complete']),
    )
    expect(result.current.items[1].message?.subject).toBe('segundo.msg')
    act(() => result.current.retry(result.current.items[0].id))
    await waitFor(() => expect(result.current.items[0].status).toBe('complete'))
    expect(mocks.extractMessage).toHaveBeenCalledTimes(3)
  })

  it('no revive selección ni archivos si se limpia la sesión durante una extracción', async () => {
    let resolve!: (value: ExtractionResponse) => void
    mocks.extractMessage.mockImplementationOnce(
      () =>
        new Promise<ExtractionResponse>((complete) => {
          resolve = complete
        }),
    )
    mocks.extractMessage.mockResolvedValueOnce(response('nuevo.msg'))
    const { result } = renderHook(() => useExtractionQueue())

    act(() => result.current.addFiles([new File(['a'], 'lento.msg')]))
    await waitFor(() => expect(result.current.items[0]?.status).toBe('extracting'))
    act(() => result.current.clear())
    act(() => resolve(response('lento.msg')))
    await waitFor(() => expect(result.current.items).toEqual([]))
    expect(result.current.selectedId).toBeNull()

    act(() => result.current.addFiles([new File(['b'], 'nuevo.msg')]))
    await waitFor(() => expect(result.current.items[0]?.status).toBe('complete'))
    expect(result.current.selectedId).toBe(result.current.items[0].id)
  })
})
