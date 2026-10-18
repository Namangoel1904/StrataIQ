import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, ChevronLeft, ChevronRight, FileSpreadsheet, FileText, X } from 'lucide-react'
import { DisplayCard, stackClass } from '@/components/ui/display-cards'
import { prettyDocName } from '@/lib/format'
import type { DocumentItem } from '@/lib/types'
import { cn } from '@/lib/utils'

interface DocumentDeckProps {
  docs: DocumentItem[]
  pointed: string[]
  onToggle: (docId: string) => void
  onClear: () => void
}

const PER_PAGE = 3
const TYPES = ['ALL', 'PDF', 'DOCX', 'CSV'] as const
// Natural size of the 3-card stack: card (22rem) + two 4rem offsets, and its stacked height.
const STACK_W = 480
const STACK_H = 330

/** Scales the fixed-size skewed stack down to whatever width the column gives it. */
function useFitScale() {
  const ref = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(1)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setScale(Math.min(1, e.contentRect.width / (STACK_W + 24))))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return { ref, scale }
}

export default function DocumentDeck({ docs, pointed, onToggle, onClear }: DocumentDeckProps) {
  const [type, setType] = useState<(typeof TYPES)[number]>('ALL')
  const [page, setPage] = useState(0)
  const { ref, scale } = useFitScale()

  const filtered = useMemo(() => docs.filter((d) => type === 'ALL' || d.file_type === type), [docs, type])
  const pages = Math.max(1, Math.ceil(filtered.length / PER_PAGE))
  const safePage = Math.min(page, pages - 1)
  const slice = filtered.slice(safePage * PER_PAGE, safePage * PER_PAGE + PER_PAGE)

  useEffect(() => setPage(0), [type, docs])

  // Keep the stack visually full even on a short last page (cards fill from the back).
  const start = PER_PAGE - slice.length
  const pointedDocs = pointed.map((id) => docs.find((d) => d.doc_id === id)).filter((d): d is DocumentItem => !!d)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2 px-1">
        {TYPES.map((t) => (
          <button
            key={t}
            onClick={() => setType(t)}
            aria-pressed={type === t}
            className={cn(
              'rounded-full px-3.5 py-1.5 text-xs font-semibold transition-colors',
              type === t ? 'bg-primary text-primary-foreground' : 'bg-muted/70 text-muted-foreground hover:text-foreground',
            )}
          >
            {t === 'ALL' ? `All ${docs.length}` : t}
          </button>
        ))}
        <span className="ml-auto text-xs tabular-nums text-muted-foreground">
          {filtered.length === 0 ? '0' : `${safePage * PER_PAGE + 1}–${Math.min(filtered.length, (safePage + 1) * PER_PAGE)}`} of {filtered.length}
        </span>
      </div>

      {/* stage */}
      <div ref={ref} className="relative w-full overflow-visible" style={{ height: STACK_H * scale }}>
        <div key={`${type}-${safePage}`} className="absolute left-0 top-0 origin-top-left pt-10" style={{ transform: `scale(${scale})`, width: STACK_W }}>
          <div className="grid animate-in fade-in-0 slide-in-from-right-6 duration-500 [grid-template-areas:'stack']">
            {slice.map((d, i) => {
              const idx = start + i
              const selected = pointed.includes(d.doc_id)
              const isPdfLike = d.file_type !== 'CSV'
              const Icon = isPdfLike ? FileText : FileSpreadsheet
              return (
                <DisplayCard
                  key={d.doc_id}
                  title={prettyDocName(d.file_name)}
                  description={`${d.dept_id.replace('DEPT-', '')} · ${d.version}`}
                  date={`${d.file_type} · ${d.chunk_count} chunks · L${d.min_layer_clearance}+`}
                  icon={selected ? <Check className="size-4 text-emerald-200" /> : <Icon className="size-4 text-blue-300" />}
                  iconClassName={selected ? '!bg-emerald-700' : undefined}
                  titleClassName={selected ? 'text-sky' : 'text-blue-500'}
                  selected={selected}
                  onClick={() => onToggle(d.doc_id)}
                  className={stackClass(idx, !selected && idx !== 2)}
                />
              )
            })}
          </div>
        </div>
        {filtered.length === 0 && <p className="absolute inset-0 grid place-items-center text-sm text-muted-foreground">No documents of this type.</p>}
      </div>

      {/* pager */}
      <div className="flex items-center justify-between gap-3">
        <button className="round-btn !size-10" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={safePage === 0} aria-label="Previous documents">
          <ChevronLeft className="size-5" />
        </button>
        <div className="flex items-center gap-1.5" aria-hidden="true">
          {Array.from({ length: pages }, (_, i) => (
            <span key={i} className={cn('h-1.5 rounded-full transition-all', i === safePage ? 'w-6 bg-primary' : 'w-1.5 bg-border')} />
          ))}
        </div>
        <button className="round-btn !size-10" onClick={() => setPage((p) => Math.min(pages - 1, p + 1))} disabled={safePage >= pages - 1} aria-label="Next documents">
          <ChevronRight className="size-5" />
        </button>
      </div>

      {/* what's pointed */}
      <div className="min-h-[2.25rem]">
        {pointedDocs.length === 0 ? (
          <p className="text-center text-xs text-muted-foreground">Click a card to point the agent at it. Hover a faded one to bring it forward.</p>
        ) : (
          <div className="flex flex-wrap items-center gap-1.5">
            {pointedDocs.map((d) => (
              <button
                key={d.doc_id}
                onClick={() => onToggle(d.doc_id)}
                className="group inline-flex max-w-full items-center gap-1.5 rounded-full bg-sky/20 py-1 pl-3 pr-2 text-xs font-semibold"
                title={`Unpoint ${d.file_name}`}
              >
                <span className="truncate">{prettyDocName(d.file_name)}</span>
                <X className="size-3.5 shrink-0 opacity-60 group-hover:opacity-100" />
              </button>
            ))}
            <button onClick={onClear} className="px-2 text-xs font-medium text-muted-foreground hover:text-foreground">
              Clear
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
