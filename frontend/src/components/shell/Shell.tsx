import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Bell, FolderOpen, LayoutGrid, Layers, Mic, Moon, RotateCcw, ShieldCheck, Sun, type LucideIcon } from 'lucide-react'
import { api } from '@/lib/api'
import { deriveAlerts } from '@/lib/alerts'
import { cn } from '@/lib/utils'
import { useSession, type View } from '@/state/session'
import Avatar from './Avatar'
import DevDeskToggle from '@/components/dev/DevDeskToggle'

const NAV: { view: View; label: string; icon: LucideIcon }[] = [
  { view: 'overview', label: 'Overview', icon: LayoutGrid },
  { view: 'documents', label: 'Documents', icon: FolderOpen },
  { view: 'talk', label: 'Talk to Docs', icon: Mic },
]

function Logo() {
  return (
    <div className="flex items-center gap-2.5 select-none">
      <span className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
        <Layers className="size-5" strokeWidth={2} />
      </span>
      <span className="text-[1.65rem] leading-none tracking-tight">
        <span className="font-bold">Strata</span>
        <span className="font-light">IQ</span>
      </span>
    </div>
  )
}

function AlertsButton() {
  const { boot } = useSession()
  const alerts = useMemo(() => deriveAlerts(boot.data), [boot.data])
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false)
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div ref={ref} className="relative">
      <button className="round-btn relative" onClick={() => setOpen((o) => !o)} aria-label={`Alerts (${alerts.length})`} aria-expanded={open}>
        <Bell className="size-5" strokeWidth={1.6} />
        {alerts.length > 0 && <span className="absolute right-3 top-3 size-2 rounded-full bg-coral ring-2 ring-background" />}
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.16 }}
            className="glass absolute right-0 top-14 z-50 w-80 rounded-2xl bg-card p-2 shadow-2xl"
            style={{ background: 'var(--panel-solid)' }}
          >
            <p className="px-3 pb-1 pt-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">Needs attention</p>
            {alerts.length === 0 && <p className="px-3 py-4 text-sm text-muted-foreground">You&apos;re all caught up.</p>}
            {alerts.map((a) => (
              <div key={a.id} className="flex gap-3 rounded-xl px-3 py-2.5 hover:bg-muted">
                <span className={cn('mt-1.5 size-2 shrink-0 rounded-full', a.tone === 'critical' ? 'bg-coral' : a.tone === 'warning' ? 'bg-amber-soft' : 'bg-sky')} />
                <div className="min-w-0">
                  <p className="text-sm font-semibold leading-snug">{a.title}</p>
                  <p className="text-xs leading-snug text-muted-foreground">{a.detail}</p>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ResetButton() {
  const { boot, docs } = useSession()
  const [busy, setBusy] = useState(false)
  return (
    <button
      className="round-btn"
      title="Reset demo state"
      aria-label="Reset demo state"
      disabled={busy}
      onClick={async () => {
        setBusy(true)
        try {
          await api.resetDemo()
          boot.reload()
          docs.reload()
        } finally {
          setBusy(false)
        }
      }}
    >
      <RotateCcw className={cn('size-5', busy && 'animate-spin')} strokeWidth={1.6} />
    </button>
  )
}

export default function Shell({ children }: { children: ReactNode }) {
  const { view, go, theme, toggleTheme, boot, userId } = useSession()
  const me = boot.data?.user_profile

  return (
    <div className="app-bg min-h-screen">
      <div className="mx-auto max-w-[1760px] px-4 pb-24 pt-4 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-4 py-2">
          <Logo />

          <nav className="glass hidden rounded-full p-1.5 md:flex" aria-label="Primary">
            {NAV.map((n) => {
              const active = view === n.view
              return (
                <button
                  key={n.view}
                  onClick={() => go(n.view)}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'relative rounded-full px-5 py-2.5 text-[0.95rem] font-medium transition-colors',
                    active ? 'text-primary-foreground' : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-pill"
                      className="absolute inset-0 rounded-full bg-primary"
                      transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                    />
                  )}
                  <span className="relative">{n.label}</span>
                </button>
              )
            })}
          </nav>

          <div className="flex items-center gap-2.5">
            <span
              className="glass hidden items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold xl:inline-flex"
              title="Zero-Trust Row-Level Security: every query is scoped to this clearance"
            >
              <ShieldCheck className="size-4 text-mint" />
              Clearance L{me?.clearance_level ?? '–'}
            </span>
            <ResetButton />
            <AlertsButton />
            <button className="round-btn overflow-hidden p-0" onClick={() => go('overview')} aria-label="My profile">
              <Avatar userId={userId} name={me?.full_name} size={48} />
            </button>
          </div>
        </header>

        {/* mobile nav */}
        <nav className="glass mb-3 flex rounded-full p-1 md:hidden" aria-label="Primary">
          {NAV.map((n) => (
            <button
              key={n.view}
              onClick={() => go(n.view)}
              className={cn(
                'flex-1 rounded-full px-3 py-2 text-sm font-medium',
                view === n.view ? 'bg-primary text-primary-foreground' : 'text-muted-foreground',
              )}
            >
              {n.label}
            </button>
          ))}
        </nav>

        <div className="flex gap-5 pt-2">
          <aside className="sticky top-5 hidden h-[calc(100vh-2.5rem)] shrink-0 flex-col items-center gap-3 lg:flex">
            {NAV.map((n) => {
              const Icon = n.icon
              const active = view === n.view
              return (
                <button
                  key={n.view}
                  className={cn('round-btn', active && '!bg-primary !text-primary-foreground')}
                  onClick={() => go(n.view)}
                  title={n.label}
                  aria-label={n.label}
                  aria-current={active ? 'page' : undefined}
                >
                  <Icon className="size-5" strokeWidth={1.6} />
                </button>
              )
            })}
            <div className="mt-auto flex flex-col gap-3 pb-6">
              <button
                className={cn('round-btn', theme === 'dark' && '!bg-primary !text-primary-foreground')}
                onClick={() => theme !== 'dark' && toggleTheme()}
                aria-label="Dark theme"
                aria-pressed={theme === 'dark'}
              >
                <Moon className="size-5" strokeWidth={1.6} />
              </button>
              <button
                className={cn('round-btn', theme === 'light' && '!bg-primary !text-primary-foreground')}
                onClick={() => theme !== 'light' && toggleTheme()}
                aria-label="Light theme"
                aria-pressed={theme === 'light'}
              >
                <Sun className="size-5" strokeWidth={1.6} />
              </button>
            </div>
          </aside>

          <main className="min-w-0 flex-1 pb-44">
            <AnimatePresence mode="wait">
              <motion.div
                key={view}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.28, ease: [0.2, 0.8, 0.2, 1] }}
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
      <DevDeskToggle />
    </div>
  )
}
