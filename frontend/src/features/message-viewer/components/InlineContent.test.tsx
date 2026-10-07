import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { HighlightContext } from '../highlight'
import { InlineContent } from './InlineContent'

const renderText = (text: string, terms: string[] = []) =>
  render(
    <HighlightContext.Provider value={terms}>
      <InlineContent text={text} attachments={[]} onOpenAttachment={() => undefined} />
    </HighlightContext.Provider>,
  )

describe('InlineContent', () => {
  it('muestra las direcciones web del texto como enlaces que se abren aparte', () => {
    renderText('Revisa el informe final <https://contoso.example.test/informe?id=7>.\n\nGracias.')
    const link = screen.getByRole('link', { name: 'https://contoso.example.test/informe?id=7' })
    expect(link).toHaveAttribute('href', 'https://contoso.example.test/informe?id=7')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
    expect(link.closest('p')?.textContent).toBe(
      'Revisa el informe final <https://contoso.example.test/informe?id=7>.',
    )
  })

  it('resalta la búsqueda también dentro de un enlace y no enlaza otros esquemas', () => {
    renderText('Portal https://obra.example.test/planos y javascript:alert(1)', ['planos'])
    const link = screen.getByRole('link')
    expect(within(link).getByText('planos').tagName).toBe('MARK')
    expect(screen.getAllByRole('link')).toHaveLength(1)
  })
})
