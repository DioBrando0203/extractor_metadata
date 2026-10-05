import { afterEach, describe, expect, it, vi } from 'vitest'
import { extractMessage } from './api'

describe('extractMessage', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('normaliza el contrato ampliado sin perder los campos existentes', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          message: {
            status: 'partial',
            subject: 'Aviso',
            body: 'Texto',
            body_truncated: true,
            headers: [{ name: 'Message-ID', value: '<1>' }],
            properties: [{ label: 'Clase', value: 'IPM.Note' }],
            attachments: [{ filename: 'plano.dwg', size: 42, metadata: [{ key: 'Versión', value: '2018' }] }],
            warnings: ['Adjunto parcial'],
            recipients: ['Para: equipo@example.test', 'CC: copia@example.test', 'CCO: oculto@example.test'],
          },
          processed_locally: true,
        }),
        { status: 200 },
      ),
    )
    vi.stubGlobal('fetch', fetchMock)

    const result = await extractMessage(new File(['x'], 'correo.msg', { type: 'application/vnd.ms-outlook' }))

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/messages/extract'),
      expect.objectContaining({ method: 'POST' }),
    )
    expect(result.message).toMatchObject({
      file_name: 'correo.msg',
      subject: 'Aviso',
      status: 'partial',
      body_truncated: true,
    })
    expect(result.message.headers[0]).toMatchObject({ label: 'Message-ID', value: '<1>' })
    expect(result.message.attachments[0]).toMatchObject({ name: 'plano.dwg', size_bytes: 42 })
    expect(result.message.recipients).toEqual([
      'Para: equipo@example.test',
      'CC: copia@example.test',
      'CCO: oculto@example.test',
    ])
  })

  it('traduce un fallo de red a una recomendación entendible', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    await expect(extractMessage(new File(['x'], 'correo.msg'))).rejects.toThrow(
      'No se pudo conectar con el extractor local',
    )
  })
})
