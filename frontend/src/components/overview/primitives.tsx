import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export function Panel({ className, children }: { className?: string; children: ReactNode }) {
  return <section className={cn('glass rounded-[2rem]', className)}>{children}</section>
}

export function PanelHeader({ title, right, className }: { title: ReactNode; right?: ReactNode; className?: string }) {
  return (
    <div className={cn('flex items-center justify-between gap-3 px-6 pt-6 sm:px-8', className)}>
      <h2 className="text-[1.35rem] font-semibold leading-tight tracking-tight">{title}</h2>
      {right && <div className="flex items-center gap-2">{right}</div>}
    </div>
  )
}

type Tone = 'neutral' | 'blue' | 'red' | 'green' | 'amber'
const TONES: Record<Tone, string> = {
  neutral: 'bg-muted text-muted-foreground',
  blue: 'bg-sky/20 text-[color-mix(in_srgb,var(--accent-blue)_80%,var(--foreground))]',
  red: 'bg-coral/20 text-[color-mix(in_srgb,var(--accent-red)_85%,var(--foreground))]',
  green: 'bg-mint/20 text-[color-mix(in_srgb,var(--accent-green)_85%,var(--foreground))]',
  amber: 'bg-amber-soft/20 text-[color-mix(in_srgb,var(--accent-amber)_85%,var(--foreground))]',
}

export function Chip({ tone = 'neutral', children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return (
    <span className={cn('inline-flex items-center gap-1 whitespace-nowrap rounded-full px-3 py-1 text-xs font-semibold', TONES[tone], className)}>
      {children}
    </span>
  )
}

export function Stat({ label, value, sub, tone }: { label: string; value: ReactNode; sub?: ReactNode; tone?: Tone }) {
  return (
    <div className="min-w-0">
      <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={cn('mt-1 text-2xl font-semibold tracking-tight tabular-nums', tone === 'red' && 'text-coral')}>{value}</p>
      {sub && <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p>}
    </div>
  )
}

export interface DonutSlice {
  label: string
  value: number
  color: string
}

/** Inspiration-style big ring chart with a centred figure and a legend. */
export function Donut({ slices, center, caption }: { slices: DonutSlice[]; center: ReactNode; caption?: ReactNode }) {
  const total = slices.reduce((a, s) => a + s.value, 0)
  const R = 62
  const C = 2 * Math.PI * R
  let offset = 0
  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:gap-8">
      <div className="relative size-48 shrink-0">
        <svg viewBox="0 0 160 160" className="size-full -rotate-90">
          <circle cx="80" cy="80" r={R} fill="none" stroke="var(--muted)" strokeWidth="22" />
          {total > 0 &&
            slices.map((s) => {
              const len = (s.value / total) * C
              const el = (
                <circle
                  key={s.label}
                  cx="80"
                  cy="80"
                  r={R}
                  fill="none"
                  stroke={s.color}
                  strokeWidth="22"
                  strokeDasharray={`${Math.max(0, len - 3)} ${C}`}
                  strokeDashoffset={-offset}
                  strokeLinecap="butt"
                  className="transition-[stroke-dasharray] duration-700"
                />
              )
              offset += len
              return el
            })}
        </svg>
        <div className="absolute inset-0 grid place-items-center text-center">
          <div>
            <div className="text-3xl font-semibold tabular-nums">{center}</div>
            {caption && <div className="text-xs text-muted-foreground">{caption}</div>}
          </div>
        </div>
      </div>
      <ul className="w-full min-w-0 space-y-2.5">
        {slices.map((s) => (
          <li key={s.label} className="flex items-center gap-3 text-sm">
            <span className="size-3 shrink-0 rounded-full" style={{ background: s.color }} />
            <span className="min-w-0 flex-1 truncate text-muted-foreground">{s.label}</span>
            <span className="font-semibold tabular-nums">{s.value}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
