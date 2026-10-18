import { useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { AlertTriangle, ArrowRight, CheckCircle2, Clock, Loader2, Mic, Sparkles, Stethoscope } from 'lucide-react'
import { api } from '@/lib/api'
import { humanize, inr, inrCompact } from '@/lib/format'
import { useAsync } from '@/lib/hooks'
import type { BootstrapResponse, ClaimItem, ConflictAlert, DecisionMatrixItem, LowerKPIs, MiddleKPIs, UpperKPIs } from '@/lib/types'
import { cn } from '@/lib/utils'
import { useSession } from '@/state/session'
import { Chip, Donut, Panel, PanelHeader, type DonutSlice } from './primitives'

const fmtDate = (iso: string) =>
  new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })

/* ───────────────────────── UPPER · Executive decision matrix ───────────────────────── */

export function DecisionPanel() {
  const { userId, boot } = useSession()
  const decisions = useAsync(() => api.decisions(), [userId])
  const [picked, setPicked] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const dec: DecisionMatrixItem | undefined = decisions.data?.decisions[0]
  const canApprove = !!dec && dec.approver_user_id === userId && dec.status.startsWith('PENDING')
  const done = !!dec && !dec.status.startsWith('PENDING')

  const approve = async () => {
    if (!dec || !picked) return
    setBusy(true)
    setError(null)
    try {
      await api.approveDecision(dec.decision_id, picked)
      setPicked(null)
      decisions.reload()
      boot.reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Approval failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel className="pb-6">
      <PanelHeader
        title="Executive Decision Matrix"
        right={dec && <Chip tone={done ? 'green' : 'amber'}>{done ? 'Executed' : 'Awaiting approval'}</Chip>}
      />
      {!dec ? (
        <p className="px-8 py-10 text-sm text-muted-foreground">{decisions.loading ? 'Loading decisions…' : 'No decisions require your attention.'}</p>
      ) : (
        <div className="px-6 pt-4 sm:px-8">
          <p className="text-sm text-muted-foreground">{dec.title}</p>
          <div className="mt-4 grid gap-3 lg:grid-cols-3">
            {dec.options.map((o) => {
              const recommended = o.option_code.includes('RECOMMENDED')
              const chosen = done ? dec.selected_option === o.option_code : picked === o.option_code
              return (
                <button
                  key={o.option_code}
                  disabled={!canApprove}
                  onClick={() => setPicked(o.option_code)}
                  aria-pressed={chosen}
                  className={cn(
                    'relative flex flex-col gap-3 rounded-2xl border p-4 text-left transition-all',
                    'border-white/70 bg-card/80 dark:border-white/5 dark:bg-card/60',
                    canApprove && 'hover:-translate-y-0.5',
                    chosen && 'border-primary/80 shadow-[0_14px_30px_-18px_rgba(0,0,0,0.5)] ring-1 ring-primary/60',
                    !chosen && done && 'opacity-50',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-[0.7rem] uppercase tracking-wider text-muted-foreground">{o.option_code.replace('_RECOMMENDED', '')}</span>
                    {recommended && (
                      <Chip tone="green">
                        <Sparkles className="size-3" /> Recommended
                      </Chip>
                    )}
                  </div>
                  <p className="text-[0.88rem] font-semibold leading-snug">{o.label}</p>
                  <dl className="mt-auto space-y-1.5 text-xs">
                    <div className="flex justify-between gap-3">
                      <dt className="text-muted-foreground">Company cost</dt>
                      <dd className="font-semibold tabular-nums">{inrCompact(o.net_company_cost_inr)}</dd>
                    </div>
                    <div className="flex justify-between gap-3">
                      <dt className="text-muted-foreground">Employee impact</dt>
                      <dd className="font-semibold tabular-nums">{o.employee_monthly_impact_inr ? `${inr(o.employee_monthly_impact_inr)}/mo` : 'None'}</dd>
                    </div>
                  </dl>
                  <p className="border-t border-border/70 pt-2 text-xs text-muted-foreground">{o.cutoff_resolution}</p>
                  <p className="text-xs text-muted-foreground/90">
                    <span className="font-semibold text-foreground">Risk · </span>
                    {o.risk_level}
                  </p>
                </button>
              )
            })}
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            {canApprove ? (
              <>
                <button
                  onClick={approve}
                  disabled={!picked || busy}
                  className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
                >
                  {busy ? <Loader2 className="size-4 animate-spin" /> : <CheckCircle2 className="size-4" />}
                  Approve &amp; execute
                </button>
                <p className="text-xs text-muted-foreground">
                  {picked ? 'Runs one ACID transaction: logs the decision and resolves the blocked task.' : 'Select an option to approve. AI recommends, you decide.'}
                </p>
              </>
            ) : (
              <p className="text-xs text-muted-foreground">
                {done
                  ? `Approved ${humanize(dec.selected_option)}${dec.decided_at ? ` · ${new Date(dec.decided_at).toLocaleString('en-IN')}` : ''}.`
                  : 'Read-only: this decision belongs to another approver.'}
              </p>
            )}
          </div>
          {error && <p className="mt-3 text-sm text-coral">{error}</p>}
        </div>
      )}
    </Panel>
  )
}

/* ───────────────────────── MIDDLE · Cross-silo conflict ───────────────────────── */

function TaskNode({ id, title, due, tone }: { id: string; title: string; due: string; tone: 'red' | 'blue' }) {
  return (
    <div className="min-w-0 flex-1 rounded-2xl border border-white/70 bg-card/80 p-4 dark:border-white/5 dark:bg-card/60">
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-xs text-muted-foreground">{id}</span>
        <Chip tone={tone}>
          <Clock className="size-3" /> {fmtDate(due)}
        </Chip>
      </div>
      <p className="mt-2 text-sm font-semibold leading-snug">{title}</p>
    </div>
  )
}

export function ConflictPanel({ conflict }: { conflict: ConflictAlert | null }) {
  const { catalog, ask } = useSession()
  const prompt = catalog.data?.sample_voice_prompts[0]
  const gap = conflict ? Math.round((+new Date(conflict.task_b_due) - +new Date(conflict.task_a_due)) / 864e5) : 0
  return (
    <Panel className="pb-6">
      <PanelHeader
        title="Cross-Silo Schedule Collision"
        right={<Chip tone={conflict ? 'red' : 'green'}>{conflict ? 'Collision detected' : 'All clear'}</Chip>}
      />
      <div className="px-6 pt-4 sm:px-8">
        {conflict ? (
          <>
            <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center">
              <TaskNode id={conflict.task_a_id} title={conflict.task_a_title} due={conflict.task_a_due} tone="red" />
              <div className="flex shrink-0 flex-col items-center gap-1 px-1 text-coral" aria-label={`${gap} day gap`}>
                <AlertTriangle className="size-5" />
                <div className="hidden h-px w-16 border-t-2 border-dashed border-coral md:block" />
                <span className="text-xs font-semibold">{gap}-day gap</span>
              </div>
              <TaskNode id={conflict.task_b_id} title={conflict.task_b_title} due={conflict.task_b_due} tone="blue" />
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">{conflict.description}</p>
            <div className="mt-4 flex flex-wrap items-center gap-2.5">
              <Chip tone="red">{conflict.employees_blocked} employees blocked</Chip>
              <Chip tone="amber">{inrCompact(conflict.claims_amount_inr)} claims at risk</Chip>
              {prompt && (
                <button
                  onClick={() => ask(prompt.spoken_text, prompt.pointed_doc_ids)}
                  className="ml-auto inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
                >
                  <Mic className="size-4" /> Ask StrataIQ <ArrowRight className="size-4" />
                </button>
              )}
            </div>
          </>
        ) : (
          <p className="flex items-center gap-2 py-8 text-sm text-muted-foreground">
            <CheckCircle2 className="size-5 text-mint" />
            No schedule collisions. The payroll lock and SSO launch are aligned.
          </p>
        )}
      </div>
    </Panel>
  )
}

/* ───────────────────────── LOWER · Personal benefits ───────────────────────── */

export function BenefitsPanel({ kpis }: { kpis: LowerKPIs }) {
  const { boot, docs } = useSession()
  const e = kpis.enrollment
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)
  const pending = e?.parental_opt_in === 'PENDING_CONFIRMATION'

  const confirm = async () => {
    setBusy(true)
    try {
      const r = await api.confirmRider()
      setMsg(r.message)
      boot.reload()
      docs.reload()
    } catch (err) {
      setMsg(err instanceof Error ? err.message : 'Could not confirm')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Panel className="pb-6">
      <PanelHeader title="My Health Benefits" right={e && <Chip tone="blue">{e.policy_id}</Chip>} />
      <div className="px-6 pt-4 sm:px-8">
        {e ? (
          <>
            <div
              className={cn(
                'flex flex-col gap-4 rounded-2xl p-5 sm:flex-row sm:items-center',
                pending ? 'bg-coral/10 ring-1 ring-coral/30' : 'bg-mint/10 ring-1 ring-mint/30',
              )}
            >
              <span className={cn('grid size-12 shrink-0 place-items-center rounded-2xl', pending ? 'bg-coral/20 text-coral' : 'bg-mint/20 text-mint')}>
                {pending ? <AlertTriangle className="size-6" /> : <CheckCircle2 className="size-6" />}
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-semibold">Parental rider · {humanize(e.parental_opt_in)}</p>
                <p className="text-sm text-muted-foreground">
                  {pending
                    ? 'Confirm before Oct 22 so your parents stay covered for cashless hospitalisation under NovaShield.'
                    : `Migration status: ${humanize(e.migration_status)}.`}
                </p>
              </div>
              {pending && (
                <button
                  onClick={confirm}
                  disabled={busy}
                  className="inline-flex shrink-0 items-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
                >
                  {busy && <Loader2 className="size-4 animate-spin" />}
                  Confirm rider
                </button>
              )}
            </div>
            {msg && <p className="mt-2 text-sm text-muted-foreground">{msg}</p>}
            <dl className="mt-5 grid grid-cols-3 gap-4">
              {[
                ['Sum insured', inrCompact(e.sum_insured)],
                ['Dependents', String(e.dependents_count)],
                ['Monthly co-pay', `₹${e.monthly_copay_deduction.toLocaleString('en-IN')}`],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs uppercase tracking-wider text-muted-foreground">{k}</dt>
                  <dd className="mt-1 text-2xl font-semibold tabular-nums">{v}</dd>
                </div>
              ))}
            </dl>
          </>
        ) : (
          <p className="py-8 text-sm text-muted-foreground">No enrollment record found.</p>
        )}

        {kpis.assigned_tasks.length > 0 && (
          <div className="mt-6">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">My tasks</p>
            <ul className="space-y-2">
              {kpis.assigned_tasks.map((t) => (
                <li key={t.task_id} className="flex items-center gap-3 rounded-xl bg-muted/70 px-4 py-2.5 text-sm">
                  <span className="font-mono text-xs text-muted-foreground">{t.task_id}</span>
                  <span className="min-w-0 flex-1 truncate font-medium">{t.title}</span>
                  <span className="hidden text-xs text-muted-foreground sm:inline">{fmtDate(t.due_date)}</span>
                  <Chip tone={t.blocker_note ? 'red' : 'neutral'}>{humanize(t.status)}</Chip>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Panel>
  )
}

/* ───────────────────────── Shared: ring chart, claims, history ───────────────────────── */

export function RolePulse({ boot }: { boot: BootstrapResponse }) {
  const { slices, center, caption, title } = useMemo(() => pulseFor(boot), [boot])
  return (
    <Panel className="pb-8">
      <PanelHeader title={title} />
      <div className="px-6 pt-6 sm:px-8">
        <Donut slices={slices} center={center} caption={caption} />
      </div>
    </Panel>
  )
}

function pulseFor(boot: BootstrapResponse): { title: string; slices: DonutSlice[]; center: string; caption: string } {
  const k = boot.role_scoped_kpis
  if (boot.user_profile.layer_code === 'UPPER') {
    const u = k as UpperKPIs
    const covered = Math.min(u.legacycare_prorata_refund_inr, u.parental_premium_variance_inr)
    const rest = Math.max(0, u.parental_premium_variance_inr - covered)
    const pct = u.parental_premium_variance_inr ? Math.round((covered / u.parental_premium_variance_inr) * 100) : 0
    return {
      title: 'Variance Coverage',
      center: `${pct}%`,
      caption: 'covered by refund',
      slices: [
        { label: `LegacyCare refund · ${inrCompact(covered)}`, value: Math.round(covered / 1000), color: 'var(--accent-blue)' },
        { label: `Uncovered · ${inrCompact(rest)}`, value: Math.round(rest / 1000), color: 'var(--accent-red)' },
      ],
    }
  }
  if (boot.user_profile.layer_code === 'MIDDLE') {
    const m = k as MiddleKPIs
    return {
      title: 'Stuck Claims',
      center: String(m.stuck_transition_claims_count),
      caption: 'in transition',
      slices: [
        { label: 'P0 / P1 escalations', value: m.p0_p1_escalations, color: 'var(--accent-red)' },
        { label: 'Standard', value: Math.max(0, m.stuck_transition_claims_count - m.p0_p1_escalations), color: 'var(--accent-blue)' },
      ],
    }
  }
  const l = k as LowerKPIs
  const by = new Map<string, number>()
  for (const t of l.assigned_tasks) by.set(t.status, (by.get(t.status) ?? 0) + 1)
  const palette = ['var(--accent-blue)', 'var(--accent-red)', 'var(--accent-green)', 'var(--accent-amber)']
  const slices = [...by.entries()].map(([s, v], i) => ({ label: humanize(s), value: v, color: palette[i % palette.length] }))
  return { title: 'My Task Status', center: String(l.assigned_tasks.length), caption: 'assigned tasks', slices }
}

export function ClaimsPanel({ claims }: { claims: ClaimItem[] }) {
  return (
    <Panel className="pb-6">
      <PanelHeader title="My Claims & Pre-Auth Tracker" right={<Chip>{claims.length} on file</Chip>} />
      <div className="mt-4 overflow-x-auto px-3 sm:px-5">
        {claims.length === 0 ? (
          <p className="px-4 py-8 text-sm text-muted-foreground">No claims on file for you.</p>
        ) : (
          <table className="w-full min-w-[34rem] text-left text-sm">
            <thead className="text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Hospital</th>
                <th className="px-3 py-2 font-medium">Treatment</th>
                <th className="px-3 py-2 font-medium">Amount</th>
                <th className="px-3 py-2 font-medium">Stage</th>
              </tr>
            </thead>
            <tbody>
              {claims.map((c) => (
                <tr key={c.claim_id} className="border-t border-border/70">
                  <td className="px-3 py-3">
                    <p className="flex items-center gap-2 font-medium">
                      <Stethoscope className="size-4 text-muted-foreground" />
                      {c.hospital_name}
                    </p>
                    <p className="ml-6 text-xs text-muted-foreground">{c.city}</p>
                  </td>
                  <td className="px-3 py-3">{humanize(c.treatment_type)}</td>
                  <td className="px-3 py-3 font-semibold tabular-nums">{inrCompact(c.claim_amount)}</td>
                  <td className="px-3 py-3">
                    <Chip tone={c.blocker_reason && c.blocker_reason !== 'NONE' ? 'red' : 'blue'}>{humanize(c.claim_stage)}</Chip>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Panel>
  )
}

export function RecentQueries() {
  const { boot, ask } = useSession()
  const rows = useMemo(() => {
    const seen = new Set<string>()
    return (boot.data?.user_profile.ui_preferences.recent_queries ?? []).filter((q) => (seen.has(q.query) ? false : (seen.add(q.query), true)))
  }, [boot.data])

  return (
    <Panel className="pb-5">
      <PanelHeader title="Suggested Knowledge" right={<Chip>{rows.length} recent</Chip>} />
      <div className="mt-3 overflow-x-auto px-3 sm:px-5">
        <AnimatePresence initial={false}>
          {rows.length === 0 ? (
            <p className="px-3 py-6 text-sm text-muted-foreground">Nothing yet. Ask a question and it will show up here.</p>
          ) : (
            <table className="w-full min-w-[30rem] text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Subject</th>
                  <th className="px-3 py-2 font-medium">Intent</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {rows.map((q) => (
                  <motion.tr key={q.query} layout className="border-t border-border/70">
                    <td className="px-3 py-3 font-medium">{q.query}</td>
                    <td className="px-3 py-3">
                      <Chip tone="blue">{humanize(q.intent ?? 'GENERAL')}</Chip>
                    </td>
                    <td className="px-3 py-3 text-right">
                      <button onClick={() => ask(q.query)} className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold hover:bg-muted">
                        Ask again <ArrowRight className="size-3.5" />
                      </button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          )}
        </AnimatePresence>
      </div>
    </Panel>
  )
}
