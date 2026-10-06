import { findRanges } from '../../lib/textSearch'

type Props = { text: string; terms: string[] }

/** Texto con las coincidencias de búsqueda resaltadas en `<mark>`; sin términos, texto tal cual. */
export function Highlight({ text, terms }: Props) {
  const ranges = findRanges(text, terms)
  if (!ranges.length) return <>{text}</>
  const parts = []
  let last = 0
  for (const range of ranges) {
    if (range.start > last) parts.push(text.slice(last, range.start))
    parts.push(
      <mark key={range.start} className="highlight">
        {text.slice(range.start, range.end)}
      </mark>,
    )
    last = range.end
  }
  if (last < text.length) parts.push(text.slice(last))
  return <>{parts}</>
}
