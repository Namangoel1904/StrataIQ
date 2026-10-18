import { useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { Download, FileSpreadsheet, FileText, Lock, MessageSquare, Search, type LucideIcon } from 'lucide-react'
import { api } from '@/lib/api'
import { prettyDocName } from '@/lib/format'
import type { DocumentItem } from '@/lib/types'
import { cn } from '@/lib/utils'
import { useSession } from '@/state/session'
import { Chip, Panel } from '@/components/overview/primitives'

export const FILE_META: Record<string, { icon: LucideIcon; tone: string; chip: 'red' | 'blue' | 'green' }> = {
  PDF: { icon: FileText, tone: 'text-coral', chip: 'red' },
  DOCX: { icon: FileText, tone: 'text-sky', chip: 'blue' },
  CSV: { icon: FileSpreadsheet, tone: 'text-mint', chip: 'green' },
}

const TYPES = ['ALL', 'PDF', 'DOCX', 'CSV'] as const

function DocCard({ d, i }: { d: DocumentItem; i: number }) {
  const { ask } = useSession()
  const meta = FILE_META[d.file_type] ?? FILE_META.PDF
  const Icon = meta.icon
  return (
    <motion.article
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(i * 0.025, 0.3), duration: 0.35 }}
      className="group flex flex-col gap-4 rounded-[1.5rem] border border-white/70 bg-card/80 p-5 transition-shadow hover:shadow-[0_18px_36px_-22px_rgba(30,45,100,0.55)] dark:border-white/5 dark:bg-card/60"
    >
      <div className="flex items-start gap-3">
        <span className={cn('grid size-11 shrink-0 place-items-center rounded-2xl bg-muted', meta.tone)}>
          <Icon className="size-5" strokeWidth={1.7} />
        </span>
        <div className="min-w-0 flex-1">
          <p className="line-clamp-2 text-[0.95rem] font-semibold leading-snug" title={d.file_name}>
            {prettyDocName(d.file_name)}
          </p>
          <p className="mt-0.5 font-mono text-[0.7rem] text-muted-foreground">{d.doc_id}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5">
        <Chip tone={meta.chip}>{d.file_type}</Chip>
        <Chip>{d.dept_id.replace('DEPT-', '')}</Chip>
        <Chip>{d.version}</Chip>
        <Chip>{d.chunk_count} chunks</Chip>
        <Chip>L{d.min_layer_clearance}+</Chip>
      </div>
      <div className="mt-auto flex items-center gap-2 pt-1">
        <button
          onClick={() => ask(`Summarize the key points of ${prettyDocName(d.file_name)}.`, [d.doc_id])}
          className="inline-flex flex-1 items-center justify-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
        >
          <MessageSquare className="size-4" /> Ask this doc
        </button>
        <a href={api.downloadUrl(d.doc_id)} download className="round-btn !size-10" aria-label={`Download ${d.file_name}`} title="Download original">
          <Download className="size-4" />
        </a>
      </div>
    </motion.article>
  )
}

export default function DocumentsPage() {
  const { docs, boot } = useSession()
  const [type, setType] = useState<(typeof TYPES)[number]>('ALL')
  const [q, setQ] = useState('')
  const all = docs.data?.accessible_docs ?? []
  const shown = useMemo(
    () =>
      all.filter(
        (d) => (type === 'ALL' || d.file_type === type) && (!q || prettyDocName(d.file_name).toLowerCase().includes(q.toLowerCase())),
      ),
    [all, type, q],
  )
  const level = boot.data?.user_profile.clearance_level

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4 pt-1">
        <div>
          <h1 className="text-[clamp(2rem,4vw,2.9rem)] font-semibold leading-tight tracking-tight">Document Vault</h1>
          <p className="mt-1 text-[0.95rem] text-muted-foreground">Everything your clearance allows you to read, search and talk to.</p>
        </div>
        <div className="glass flex items-center gap-2 rounded-full px-4 py-2.5 text-sm">
          <Lock className="size-4 text-muted-foreground" />
          <span className="font-semibold">{docs.data?.restricted_hidden_count ?? '–'}</span>
          <span className="text-muted-foreground">restricted at L{level ?? '–'}</span>
        </div>
      </div>

      <Panel className="p-5 sm:p-7">
        <div className="mb-6 flex flex-wrap items-center gap-3">
          <label className="glass flex min-w-[14rem] flex-1 items-center gap-2 rounded-full px-4 py-2.5 sm:max-w-sm">
            <Search className="size-4 text-muted-foreground" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search documents…"
              className="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground"
              aria-label="Search documents"
            />
          </label>
          <div className="flex gap-1.5" role="tablist" aria-label="File type">
            {TYPES.map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={type === t}
                onClick={() => setType(t)}
                className={cn(
                  'rounded-full px-4 py-2 text-sm font-medium transition-colors',
                  type === t ? 'bg-primary text-primary-foreground' : 'bg-muted/70 text-muted-foreground hover:text-foreground',
                )}
              >
                {t === 'ALL' ? 'All' : t}
              </button>
            ))}
          </div>
          <span className="ml-auto text-sm text-muted-foreground">
            {shown.length} of {all.length}
          </span>
        </div>

        {docs.loading && all.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">Loading vault…</p>
        ) : shown.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">No documents match.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
            {shown.map((d, i) => (
              <DocCard key={d.doc_id} d={d} i={i} />
            ))}
          </div>
        )}
      </Panel>
    </div>
  )
}
