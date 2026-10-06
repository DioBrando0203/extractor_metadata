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

  it('acepta sólo miniaturas raster en base64 y descarta cualquier otro data URI', async () => {
    const attachments = [
      { name: 'foto.png', preview: 'data:image/jpeg;base64,/9j/4AAQ', preview_source: 'image' },
      { name: 'plano.dwg', preview: 'data:image/jpeg;base64,/9j/', preview_source: 'embedded' },
      { name: 'logo.svg', preview: 'data:image/svg+xml;base64,PHN2Zz4=', preview_source: 'image' },
      { name: 'web.html', preview: 'data:text/html,<script>alert(1)</script>', preview_source: 'image' },
    ]
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: { attachments } }), { status: 200 })),
    )
    const { message } = await extractMessage(new File(['x'], 'correo.msg'))
    expect(message.attachments.map((item) => [item.preview_source, Boolean(item.preview)])).toEqual([
      ['image', true],
      ['embedded', true],
      [null, false],
      [null, false],
    ])
  })

  it('traduce un fallo de red a una recomendación entendible', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    await expect(extractMessage(new File(['x'], 'correo.msg'))).rejects.toThrow(
      'No se pudo conectar con el extractor local',
    )
  })
})
