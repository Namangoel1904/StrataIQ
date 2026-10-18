import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { BookOpenCheck } from 'lucide-react'
import { api } from '@/lib/api'
import { prettyDocName } from '@/lib/format'
import { useAsync } from '@/lib/hooks'
import type { Citation, DocumentChunk, VoicePrimaryCitation } from '@/lib/types'
import { cn } from '@/lib/utils'
import { Chip } from '@/components/overview/primitives'

interface CitationViewerProps {
  primary: VoicePrimaryCitation | null
  citations: Citation[]
}

const norm = (s: string) => s.toLowerCase().replace(/\s+/g, ' ').trim()

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/** Wraps the passage the answer was grounded on in <mark>; whitespace-insensitive. */
function highlight(text: string, needle?: string) {
  if (!needle) return <>{text}</>
  // Try the whole snippet first, then progressively shorter prefixes.
  for (const len of [240, 100, 45]) {
    const words = needle.trim().slice(0, len).split(/\s+/).map(escapeRe)
    if (words.length < 2) continue
    const m = new RegExp(words.join('\\s+'), 'i').exec(text)
    if (m) {
      const end = m.index + m[0].length
      return (
        <>
          {text.slice(0, m.index)}
          <mark className="rounded bg-yellow-300/70 px-0.5 text-inherit dark:bg-yellow-400/40">{text.slice(m.index, end)}</mark>
          {text.slice(end)}
        </>
      )
    }
  }
  return <>{text}</>
}

export default function CitationViewer({ primary, citations }: CitationViewerProps) {
  const docIds = useMemo(() => {
    const ids = new Set<string>()
    if (primary) ids.add(primary.doc_id)
    citations.forEach((c) => ids.add(c.doc_id))
    return [...ids]
  }, [primary, citations])

  const [active, setActive] = useState<string | null>(null)
  useEffect(() => setActive(primary?.doc_id ?? docIds[0] ?? null), [primary, docIds])

  const content = useAsync(() => (active ? api.documentContent(active) : Promise.resolve(null)), [active])
  const nameOf = (id: string) => citations.find((c) => c.doc_id === id)?.file_name ?? (primary?.doc_id === id ? primary.file_name : id)
  const targetRef = useRef<HTMLDivElement>(null)

  const isHit = (c: DocumentChunk): boolean => {
    if (primary && primary.doc_id === active) {
      if (c.section_title === primary.section_title && c.page_number === primary.page_number) return true
      if (primary.highlight_snippet && norm(c.chunk_text).includes(norm(primary.highlight_snippet).slice(0, 60))) return true
    }
    return citations.some((x) => x.doc_id === active && x.section_title === c.section_title && x.page_number === c.page_number)
  }
  const snippet = primary?.doc_id === active ? primary?.highlight_snippet : citations.find((c) => c.doc_id === active)?.snippet
  const firstHit = content.data?.chunks.find(isHit)?.chunk_id

  useEffect(() => {
    if (content.loading) return
    const t = setTimeout(() => targetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 250)
    return () => clearTimeout(t)
  }, [content.loading, firstHit, active])

  if (docIds.length === 0) {
    return (
      <div className="grid place-items-center gap-2 rounded-2xl bg-muted/50 px-6 py-10 text-center">
        <BookOpenCheck className="size-8 text-muted-foreground" strokeWidth={1.4} />
        <p className="text-sm font-medium">Cited passages appear here</p>
        <p className="max-w-xs text-xs text-muted-foreground">Ask a question and the exact paragraph behind the answer is opened and highlighted.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-1.5">
        {docIds.map((id) => (
          <button
            key={id}
            onClick={() => setActive(id)}
            className={cn(
              'max-w-full truncate rounded-full px-3 py-1 text-xs font-semibold transition-colors',
              id === active ? 'bg-primary text-primary-foreground' : 'bg-muted/70 text-muted-foreground hover:text-foreground',
            )}
            title={nameOf(id)}
          >
            {id} · {prettyDocName(nameOf(id)).slice(0, 26)}
          </button>
        ))}
      </div>

      <div className="scroll-thin max-h-[22rem] space-y-2.5 overflow-y-auto rounded-2xl bg-muted/40 p-3 pr-2">
        {content.loading && <p className="p-4 text-center text-sm text-muted-foreground">Opening document…</p>}
        {content.error && <p className="p-4 text-sm text-coral">{content.error}</p>}
        {content.data?.chunks.map((c) => {
          const hit = isHit(c)
          return (
            <Fragment key={c.chunk_id}>
              <div
                ref={c.chunk_id === firstHit ? targetRef : undefined}
                className={cn(
                  'rounded-xl border p-3.5 text-[0.82rem] leading-relaxed transition-colors',
                  hit ? 'border-yellow-400/70 bg-yellow-200/30 dark:bg-yellow-300/10' : 'border-transparent bg-card/70',
                )}
              >
                <div className="mb-1.5 flex items-center gap-2">
                  <Chip tone={hit ? 'amber' : 'neutral'}>Page {c.page_number}</Chip>
                  <span className="truncate text-xs font-semibold text-muted-foreground">{c.section_title}</span>
                </div>
                <p>{hit ? highlight(c.chunk_text, snippet) : c.chunk_text}</p>
              </div>
            </Fragment>
          )
        })}
        {content.data && content.data.chunks.length === 0 && <p className="p-4 text-sm text-muted-foreground">No extractable text in this file.</p>}
      </div>
    </div>
  )
}
