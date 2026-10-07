import { afterEach, describe, expect, it, vi } from 'vitest'
import { extractMessage, fetchAllAttachments, fetchAttachment } from './api'

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

describe('correos adjuntos y enlaces', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('normaliza el correo adjunto como un correo más y el enlace con su dirección', async () => {
    const attachments = [
      {
        name: 'Cotización',
        kind: 'message',
        size_bytes: 900,
        message: {
          subject: 'Cotización',
          sender: 'ventas@example.test',
          attachments: [{ name: 'precio.pdf' }],
        },
      },
      { name: 'Presupuesto.xlsx', kind: 'link', link: ' https://contoso.sharepoint.com/x ' },
      { name: 'raro.bin', kind: 'otro', link: 'https://no-aplica.example.test', message: { subject: 'x' } },
    ]
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: { attachments } }), { status: 200 })),
    )
    const { message } = await extractMessage(new File(['x'], 'correo.msg'))
    const [inner, cloud, other] = message.attachments
    expect(inner).toMatchObject({ kind: 'message', link: null })
    expect(inner.message).toMatchObject({
      subject: 'Cotización',
      file_name: 'Cotización.msg',
      file_size_bytes: 900,
    })
    expect(inner.message?.attachments[0]).toMatchObject({ name: 'precio.pdf', kind: 'file', message: null })
    expect(cloud).toMatchObject({ kind: 'link', link: 'https://contoso.sharepoint.com/x', message: null })
    expect(other).toMatchObject({ kind: 'file', link: null, message: null })
  })

  it('pide un adjunto de un correo adjunto con su ruta', async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(new Blob(['%PDF']), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    await fetchAttachment(new File(['x'], 'correo.msg'), 0, 'precio.pdf', { messagePath: [2, 0] })
    await fetchAttachment(new File(['x'], 'correo.msg'), 1, 'plano.dwg')
    const [first, second] = fetchMock.mock.calls.map(([, init]) => init?.body as FormData)
    expect(first.get('message_path')).toBe('2/0')
    expect(first.get('attachment_index')).toBe('0')
    expect(second.has('message_path')).toBe(false)
  })
})

describe('reuniones, contactos y tareas', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('normaliza los datos del elemento y descarta tipos desconocidos', async () => {
    const respond = (item: unknown) =>
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: { item } }), { status: 200 }))
    vi.stubGlobal(
      'fetch',
      respond({
        kind: 'meeting',
        start: '2026-10-12T15:00:00Z',
        location: ' Sala 3 ',
        fields: [{ label: 'Organizador', value: 'María' }],
      }),
    )
    const { message } = await extractMessage(new File(['x'], 'reunion.msg'))
    expect(message.item).toEqual({
      kind: 'meeting',
      start: '2026-10-12T15:00:00Z',
      end: null,
      all_day: false,
      location: 'Sala 3',
      fields: [{ group: 'Elemento', label: 'Organizador', value: 'María' }],
    })
    vi.stubGlobal('fetch', respond({ kind: 'nota-adhesiva' }))
    expect((await extractMessage(new File(['x'], 'nota.msg'))).message.item).toBeNull()
  })
})

describe('correos S/MIME', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('acepta sólo los valores de seguridad conocidos', async () => {
    const respond = (security: unknown) =>
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: { security } }), { status: 200 }))
    vi.stubGlobal('fetch', respond('encrypted'))
    expect((await extractMessage(new File(['x'], 'a.msg'))).message.security).toBe('encrypted')
    vi.stubGlobal('fetch', respond('valid-signature'))
    expect((await extractMessage(new File(['x'], 'a.msg'))).message.security).toBeNull()
  })
})

describe('descargar todo', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('pide el ZIP con la ruta del correo adjunto y lo nombra como el MSG', async () => {
    const fetchMock = vi.fn<typeof fetch>(async () => new Response(new Blob(['PK']), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)
    const archive = await fetchAllAttachments(new File(['x'], 'Revisión de obra.msg'), [2])
    const body = fetchMock.mock.calls[0][1]?.body as FormData
    expect(fetchMock.mock.calls[0][0]).toContain('/messages/attachments')
    expect(body.get('message_path')).toBe('2')
    expect(archive.filename).toBe('Revisión de obra - adjuntos.zip')
  })
})
