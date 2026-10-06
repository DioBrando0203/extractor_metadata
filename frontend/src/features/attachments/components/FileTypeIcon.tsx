import {
  Code24Regular,
  Document24Regular,
  DocumentPdf24Regular,
  DocumentTable24Regular,
  DocumentText24Regular,
  DrawShape24Regular,
  FolderZip24Regular,
  Image24Regular,
  Mail24Regular,
  SlideText24Regular,
  Video24Regular,
} from '@fluentui/react-icons'
import type { FluentIcon } from '@fluentui/react-icons'
import type { FileKind } from '../lib/fileKind'

const ICONS: Record<FileKind, FluentIcon> = {
  pdf: DocumentPdf24Regular,
  word: DocumentText24Regular,
  excel: DocumentTable24Regular,
  slides: SlideText24Regular,
  image: Image24Regular,
  cad: DrawShape24Regular,
  archive: FolderZip24Regular,
  mail: Mail24Regular,
  text: Code24Regular,
  media: Video24Regular,
  other: Document24Regular,
}

type Props = { kind: FileKind; size?: 'sm' | 'md' | 'lg' }

/** Icono de tipo de archivo sobre fondo tenue; el color sale de los tokens `--kind-*`. */
export function FileTypeIcon({ kind, size = 'md' }: Props) {
  const Icon = ICONS[kind]
  return (
    <span className={`file-icon file-icon--${size}`} data-kind={kind} aria-hidden="true">
      <Icon />
    </span>
  )
}
