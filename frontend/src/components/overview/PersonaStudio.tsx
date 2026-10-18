import { useMemo, type ReactNode } from 'react'
import { motion } from 'motion/react'
import { ArrowUpRight, FolderOpen, Mail, Mic, ShieldCheck } from 'lucide-react'
import { inrCompact, humanize } from '@/lib/format'
import type { BootstrapResponse, LowerKPIs, MiddleKPIs, UpperKPIs } from '@/lib/types'
import { cn } from '@/lib/utils'
import { useSession } from '@/state/session'
import Avatar from '@/components/shell/Avatar'
import { Chip, Panel } from './primitives'

const LEVEL_META = {
  3: { name: 'Strategic', dot: 'bg-coral', text: 'text-coral' },
  2: { name: 'Tactical', dot: 'bg-sky', text: 'text-sky' },
  1: { name: 'Execution', dot: 'bg-mint', text: 'text-mint' },
} as const

interface Signal {
  label: string
  value: string
  sub?: string
  warn?: boolean
}

function signalsFor(boot: BootstrapResponse): Signal[] {
  const k = boot.role_scoped_kpis
  if (boot.user_profile.layer_code === 'UPPER') {
    const u = k as UpperKPIs
    return [
      { label: 'Parental premium variance', value: inrCompact(u.parental_premium_variance_inr), sub: 'unbudgeted', warn: true },
      { label: 'LegacyCare refund', value: inrCompact(u.legacycare_prorata_refund_inr), sub: 'pro-rata' },
      { label: 'NovaShield premium', value: inrCompact(u.novashield_annual_premium_inr), sub: 'annual' },
      { label: 'Pending decisions', value: String(u.pending_executive_decisions), warn: u.pending_executive_decisions > 0 },
    ]
  }
  if (boot.user_profile.layer_code === 'MIDDLE') {
    const m = k as MiddleKPIs
    return [
      { label: 'Employees blocked', value: String(m.employees_blocked_parental_rider), sub: 'parental rider', warn: m.employees_blocked_parental_rider > 0 },
      { label: 'Stuck claims', value: String(m.stuck_transition_claims_count), sub: inrCompact(m.stuck_transition_claims_amount_inr) },
      { label: 'P0 / P1 escalations', value: String(m.p0_p1_escalations), warn: m.p0_p1_escalations > 0 },
      { label: 'Schedule collision', value: m.conflict_alert ? 'Active' : 'Clear', warn: !!m.conflict_alert },
    ]
  }
  const l = k as LowerKPIs
  const e = l.enrollment
  return [
    { label: 'Sum insured', value: e ? inrCompact(e.sum_insured) : '–' },
    { label: 'Dependents', value: e ? String(e.dependents_count) : '–' },
    { label: 'Monthly co-pay', value: e ? `₹${e.monthly_copay_deduction.toLocaleString('en-IN')}` : '–' },
    { label: 'Parental rider', value: e ? humanize(e.parental_opt_in) : '–', warn: e?.parental_opt_in === 'PENDING_CONFIRMATION' },
  ]
}

function FlowCard({ title, children, last, delay = 0 }: { title: string; children: ReactNode; last?: boolean; delay?: number }) {
  return (
    <motion.div
      className="relative flex min-w-0 flex-col gap-3"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.2, 0.8, 0.2, 1] }}
    >
      <div className="relative h-full min-h-[17rem] rounded-[1.75rem] border border-white/70 bg-card/80 p-5 shadow-[0_10px_30px_-22px_rgba(30,45,100,0.5)] dark:border-white/5 dark:bg-card/70">
        {children}
        {!last && (
          <svg className="pointer-events-none absolute -right-[1.45rem] top-[38%] hidden xl:block" width="30" height="56" viewBox="0 0 30 56" aria-hidden="true">
            <path d="M3 8 C16 8 14 46 27 46" fill="none" stroke="var(--accent-blue)" strokeWidth="1.4" />
            <circle cx="3" cy="8" r="3.4" fill="var(--accent-blue)" />
            <circle cx="27" cy="46" r="3.4" fill="var(--accent-red)" />
          </svg>
        )}
      </div>
      <p className="text-center text-sm font-medium">{title}</p>
    </motion.div>
  )
}

export default function PersonaStudio() {
  const { personas, userId, switchPersona, boot, docs, catalog, go, ask } = useSession()
  const data = boot.data
  const me = data?.user_profile
  const level = (me?.clearance_level ?? 1) as 1 | 2 | 3
  const meta = LEVEL_META[level]
  const signals = useMemo(() => (data ? signalsFor(data) : []), [data])
  const accessible = docs.data?.accessible_docs.length ?? 0
  const restricted = docs.data?.restricted_hidden_count ?? 0
  const total = docs.data?.total_docs ?? 0
  const prompts = catalog.data?.sample_voice_prompts ?? []
  const stale = boot.loading && !!data

  return (
    <Panel className="relative p-0">
      {/* header with the persona strip */}
      <div className="flex flex-col gap-4 px-6 pt-6 sm:px-8 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h2 className="text-[1.5rem] font-semibold tracking-tight">Role Workspace</h2>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Judge Sandbox · simulate a logged-in employee. The layout, data and clearance re-shape instantly.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start lg:self-auto">
          <div className="glass flex items-end gap-2.5 rounded-full px-4 pb-4 pt-3 sm:gap-3.5" role="radiogroup" aria-label="Simulate employee">
            {personas.map((p) => {
              const selected = p.user_id === userId
              const lv = (LEVEL_META as Record<number, { name: string; dot: string; text: string }>)[p.clearance_level] ?? LEVEL_META[1]
              return (
                <button
                  key={p.user_id}
                  role="radio"
                  aria-checked={selected}
                  onClick={() => switchPersona(p.user_id)}
                  title={`${p.full_name} · ${p.job_title}`}
                  className="group relative rounded-full outline-offset-4"
                >
                  <motion.span
                    className={cn(
                      'block overflow-hidden rounded-full ring-2 ring-offset-2 ring-offset-transparent transition-shadow',
                      selected ? 'shadow-[0_10px_22px_-8px_rgba(30,45,100,0.6)] ring-white' : 'opacity-80 ring-transparent group-hover:opacity-100',
                    )}
                    animate={{ scale: selected ? 1.22 : 1, y: selected ? -4 : 0 }}
                    whileHover={{ scale: selected ? 1.22 : 1.1 }}
                    transition={{ type: 'spring', stiffness: 380, damping: 24 }}
                  >
                    <Avatar userId={p.user_id} name={p.full_name} size={50} />
                  </motion.span>
                  <span
                    className={cn(
                      'absolute -bottom-3 left-1/2 grid size-[1.15rem] -translate-x-1/2 place-items-center rounded-full text-[0.62rem] font-bold text-white ring-2 ring-white/90 dark:ring-card',
                      lv.dot,
                    )}
                  >
                    {p.clearance_level}
                  </span>
                </button>
              )
            })}
          </div>
          <button className="round-btn hidden sm:inline-flex" onClick={() => go('documents')} title="Document vault" aria-label="Document vault">
            <FolderOpen className="size-5" strokeWidth={1.6} />
          </button>
          <button className="round-btn hidden sm:inline-flex" onClick={() => go('talk')} title="Talk to documents" aria-label="Talk to documents">
            <Mic className="size-5" strokeWidth={1.6} />
          </button>
        </div>
      </div>

      {/* flow */}
      <div
        className={cn('grid gap-x-7 gap-y-6 p-6 pt-8 transition-opacity duration-300 sm:grid-cols-2 sm:p-8 xl:grid-cols-4', stale && 'opacity-60')}
        aria-busy={stale}
      >
        <FlowCard title="Identity" delay={0.05}>
          {me ? (
            <div className="flex h-full flex-col">
              <div className="flex items-center gap-4">
                <span className="overflow-hidden rounded-full shadow-[0_12px_24px_-10px_rgba(30,45,100,0.55)] ring-4 ring-white dark:ring-card">
                  <Avatar userId={me.user_id} name={me.full_name} size={84} />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-xl font-semibold leading-tight">{me.full_name}</p>
                  <p className="text-sm leading-snug text-muted-foreground">{me.job_title}</p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <Chip tone="blue">{me.dept_name}</Chip>
                <Chip tone={level === 3 ? 'red' : level === 2 ? 'blue' : 'green'}>{me.layer_code}</Chip>
                <Chip>Grade {me.grade_tier}</Chip>
              </div>
              <div className="mt-auto space-y-1.5 pt-4 text-sm text-muted-foreground">
                <p className="flex items-center gap-2 truncate">
                  <Mail className="size-4 shrink-0" />
                  <span className="truncate">{me.email}</span>
                </p>
                <p className="font-mono text-xs">{me.user_id}</p>
              </div>
            </div>
          ) : (
            <Skeleton />
          )}
        </FlowCard>

        <FlowCard title="Zero-Trust Clearance" delay={0.12}>
          <div className="flex h-full flex-col">
            <div className="flex items-center gap-3">
              <span className={cn('grid size-12 place-items-center rounded-2xl bg-muted', meta.text)}>
                <ShieldCheck className="size-6" strokeWidth={1.7} />
              </span>
              <div>
                <p className="text-xl font-semibold leading-tight">Level {level}</p>
                <p className="text-sm text-muted-foreground">{meta.name} clearance</p>
              </div>
            </div>
            <div className="mt-5 flex gap-1.5" aria-label={`Clearance ${level} of 3`}>
              {[1, 2, 3].map((n) => (
                <span key={n} className={cn('h-2 flex-1 rounded-full', n <= level ? meta.dot : 'bg-muted')} />
              ))}
            </div>
            <div className="mt-auto pt-5">
              <div className="mb-2 flex items-baseline justify-between text-sm">
                <span className="font-semibold">{accessible} accessible</span>
                <span className="text-muted-foreground">{restricted} restricted</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <motion.div
                  className="h-full rounded-full bg-primary"
                  initial={false}
                  animate={{ width: total ? `${(accessible / total) * 100}%` : '0%' }}
                  transition={{ type: 'spring', stiffness: 120, damping: 20 }}
                />
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                Row-Level Security hides {restricted} of {total} vault documents from this role.
              </p>
            </div>
          </div>
        </FlowCard>

        <FlowCard title="Live Signals" delay={0.19}>
          <ul className="flex h-full flex-col justify-between gap-3">
            {signals.map((s) => (
              <li key={s.label} className="flex items-baseline justify-between gap-3 border-b border-border/70 pb-2.5 last:border-0 last:pb-0">
                <span className="min-w-0 text-sm text-muted-foreground">
                  {s.label}
                  {s.sub && <span className="ml-1.5 text-xs opacity-70">· {s.sub}</span>}
                </span>
                <span className={cn('shrink-0 text-lg font-semibold tabular-nums', s.warn && 'text-coral')}>{s.value}</span>
              </li>
            ))}
            {signals.length === 0 && <Skeleton />}
          </ul>
        </FlowCard>

        <FlowCard title="Ask next" last delay={0.26}>
          <div className="grid h-full grid-cols-2 gap-2.5">
            <button
              onClick={() => go('talk')}
              className="col-span-2 flex items-center justify-between rounded-2xl bg-primary p-4 text-left text-primary-foreground transition-transform hover:-translate-y-0.5"
            >
              <span>
                <span className="block text-sm font-semibold leading-tight">Talk to your documents</span>
                <span className="text-xs opacity-70">Voice · pointed Q&amp;A</span>
              </span>
              <Mic className="size-5" />
            </button>
            {prompts.slice(0, 3).map((p, idx) => (
              <button
                key={p.spoken_text || idx}
                onClick={() => ask(p.spoken_text, p.pointed_doc_ids)}
                className={cn(
                  'group flex flex-col justify-between rounded-2xl bg-muted/80 p-3 text-left transition-all hover:-translate-y-0.5 hover:bg-muted',
                  'first:col-span-1',
                )}
                title={p.spoken_text}
              >
                <span className="line-clamp-3 text-[0.8rem] font-medium leading-snug">{p.label || p.spoken_text}</span>
                <ArrowUpRight className="mt-2 size-4 self-end text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
              </button>
            ))}
            <button onClick={() => go('documents')} className="flex flex-col justify-between rounded-2xl bg-muted/80 p-3 text-left transition-all hover:-translate-y-0.5 hover:bg-muted">
              <span className="text-[0.8rem] font-medium leading-snug">Browse document vault</span>
              <FolderOpen className="mt-2 size-4 self-end text-muted-foreground" />
            </button>
          </div>
        </FlowCard>
      </div>
    </Panel>
  )
}

function Skeleton() {
  return (
    <div className="space-y-3" aria-hidden="true">
      <div className="h-6 w-2/3 animate-pulse rounded-lg bg-muted" />
      <div className="h-4 w-1/2 animate-pulse rounded-lg bg-muted" />
      <div className="h-20 animate-pulse rounded-2xl bg-muted" />
    </div>
  )
}
