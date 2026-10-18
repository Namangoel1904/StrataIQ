import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { BookOpen, ChevronLeft, ChevronRight, Code, Crown, FileText, Lock, Mic, ShieldAlert, Users, type LucideIcon } from 'lucide-react'
import { useSession, type View } from '@/state/session'
import { cn } from '@/lib/utils'
import './userGuide.css'

interface Spread {
  title: string
  left: ReactNode
  right: ReactNode
}

function StepBadge({ n, icon: Icon }: { n: string; icon: LucideIcon }) {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-14 place-items-center rounded-2xl bg-primary text-primary-foreground">
        <Icon className="size-7" strokeWidth={1.6} />
      </span>
      <span className="font-mono text-xs uppercase tracking-[0.25em] ug-muted">{n}</span>
    </div>
  )
}

function Heading({ children }: { children: ReactNode }) {
  return <h2 className="mt-5 text-[1.9rem] font-semibold leading-tight tracking-tight">{children}</h2>
}

function Persona({ icon: Icon, name, role, text }: { icon: LucideIcon; name: string; role: string; text: string }) {
  return (
    <div className="flex gap-3 rounded-2xl p-3.5 ug-chip-bg">
      <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground">
        <Icon className="size-5" strokeWidth={1.7} />
      </span>
      <div className="min-w-0">
        <p className="text-sm font-semibold">
          {name} <span className="font-normal ug-muted">- {role}</span>
        </p>
        <p className="mt-0.5 text-[0.83rem] leading-snug ug-muted">{text}</p>
      </div>
    </div>
  )
}

function Steps({ items }: { items: ReactNode[] }) {
  return (
    <ol className="space-y-2.5">
      {items.map((it, i) => (
        <li key={i} className="flex gap-3 text-[0.9rem] leading-snug">
          <span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">{i + 1}</span>
          <span>{it}</span>
        </li>
      ))}
    </ol>
  )
}

function Outcome({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mt-5 rounded-2xl border-l-4 border-primary p-4 ug-chip-bg">
      <p className="text-xs font-semibold uppercase tracking-widest ug-muted">{title}</p>
      <div className="mt-1.5 space-y-1.5 text-[0.88rem] leading-snug">{children}</div>
    </div>
  )
}

function JumpButton({ view, personaId, children }: { view?: View; personaId?: string; children: ReactNode }) {
  const { go, switchPersona } = useSession()
  return (
    <button
      onClick={() => {
        if (personaId) switchPersona(personaId)
        if (view) go(view)
      }}
      className="inline-flex items-center gap-1.5 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition-all hover:opacity-90 hover:shadow-md"
    >
      {children}
    </button>
  )
}

const SPREADS: Spread[] = [
  {
    title: 'Welcome',
    left: (
      <>
        <StepBadge n="Quick User Guide" icon={BookOpen} />
        <Heading>Welcome to StrataIQ</Heading>
        <p className="mt-4 text-[0.95rem] leading-relaxed ug-muted">
          Think of StrataIQ as your company&apos;s intelligent co-worker. Instead of wasting hours searching through scattered files,
          spreadsheets and meeting notes, StrataIQ instantly organizes everything and tailors it to your job role.
        </p>
      </>
    ),
    right: (
      <>
        <p className="font-mono text-xs uppercase tracking-[0.25em] ug-muted">The live example</p>
        <p className="mt-3 text-[0.95rem] leading-relaxed">
          Our <strong>500-employee company is switching health insurance providers</strong> - from <em>LegacyCare</em> to <em>NovaShield</em>.
          That creates a temporary puzzle across budgets, payroll deadlines and medical claims.
        </p>
        <p className="mt-5 text-[0.95rem] leading-relaxed">You can test the entire platform in under 3 minutes, in four steps:</p>
        <ol className="mt-3 space-y-2 text-[0.9rem]">
          {['Pick your role', 'Talk with your documents', 'Test the security guardrails', 'Solve a company crisis'].map((s, i) => (
            <li key={s} className="flex items-center gap-3">
              <span className="grid size-6 place-items-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">{i + 1}</span>
              {s}
            </li>
          ))}
        </ol>
        <p className="mt-6 text-xs ug-muted">Use the arrows, or your keyboard&apos;s left and right keys, to turn the page.</p>
      </>
    ),
  },
  {
    title: 'Step 1 - Pick your role',
    left: (
      <>
        <StepBadge n="Step 1" icon={Users} />
        <Heading>Pick your role</Heading>
        <p className="mt-4 text-[0.95rem] leading-relaxed ug-muted">
          No passwords and no logging in and out. Use the avatar buttons at the very top of the screen to instantly step into someone
          else&apos;s shoes - the same question can have a different answer depending on who is asking.
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          <JumpButton view="overview" personaId="USR-LOW-ENG-005">🚀 Try Step 1: As Naman (Engineer)</JumpButton>
          <JumpButton view="overview" personaId="USR-UPPER-FIN-001">As Arvind (CFO)</JumpButton>
        </div>
      </>
    ),
    right: (
      <div className="space-y-3">
        <Persona icon={Code} name="Naman Goel" role="Engineer, Lower Layer" text="Daily tasks, personal insurance coverage (₹5 Lakhs) and medical claim updates." />
        <Persona icon={Users} name="Priya Kulkarni" role="HR Lead, Middle Layer" text="Team coordination, tracking blocked parental registrations and solving schedule conflicts." />
        <Persona icon={Crown} name="Arvind Mehta" role="CFO, Upper Layer" text="High-level budget variances, company costs and approving financial decisions." />
      </div>
    ),
  },
  {
    title: 'Step 2 - Talk with your documents',
    left: (
      <>
        <StepBadge n="Step 2" icon={Mic} />
        <Heading>Talk with your documents</Heading>
        <p className="mt-4 text-[0.95rem] leading-relaxed ug-muted">
          Ask a question out loud (or type it) and point StrataIQ at the exact documents that matter. Every answer is grounded,
          cited and scoped to your clearance.
        </p>
        <div className="mt-6">
          <JumpButton view="talk" personaId="USR-LOW-ENG-005">🚀 Try Step 2: Talk with Documents as Naman</JumpButton>
        </div>
      </>
    ),
    right: (
      <>
        <Steps
          items={[
            <>Switch to <strong>Naman Goel (Engineer)</strong>.</>,
            <>Open the <strong>Talk to Docs</strong> tab.</>,
            <>Select the employee handbook (<code>DOC-011</code>) and hospital directory (<code>DOC-010</code>) from the stacked card deck.</>,
            <>Click the microphone - or a sample question such as <em>&quot;Is Sahyadri Hospital cashless for cataract surgery and what is the limit?&quot;</em></>,
          ]}
        />
        <Outcome title="What happens">
          <p>You hear a natural voice answer (<strong>₹45,000 per eye</strong>) powered by Google AI.</p>
          <p>The screen opens the document, scrolls to the exact page and <strong>highlights the answer in bright yellow</strong> so you can verify it instantly.</p>
        </Outcome>
      </>
    ),
  },
  {
    title: 'Step 3 - Security guardrails',
    left: (
      <>
        <StepBadge n="Step 3" icon={Lock} />
        <Heading>Test the security guardrails</Heading>
        <p className="mt-4 text-[0.95rem] leading-relaxed ug-muted">
          StrataIQ applies Zero-Trust access to every document and every query. What you can see depends on your role - not on what you ask for.
        </p>
        <div className="mt-6">
          <JumpButton view="documents" personaId="USR-LOW-ENG-005">🚀 Try Step 3: Test Security Lock on DOC-008</JumpButton>
        </div>
      </>
    ),
    right: (
      <>
        <Steps
          items={[
            <>While still logged in as <strong>Naman Goel (Engineer)</strong>, try opening a restricted executive document such as the <strong>CFO Budget Memo</strong> (<code>DOC-008</code>).</>,
          ]}
        />
        <Outcome title="What happens">
          <p className="flex items-start gap-2">
            <ShieldAlert className="mt-0.5 size-4 shrink-0 text-coral" />
            <span>The system immediately blocks access with a clean security pop-up (<strong>HTTP 403</strong>).</span>
          </p>
          <p>That proves regular employees cannot view sensitive executive data.</p>
        </Outcome>
      </>
    ),
  },
  {
    title: 'Step 4 - Solve a company crisis',
    left: (
      <>
        <StepBadge n="Step 4" icon={FileText} />
        <Heading>Solve a company crisis</Heading>
        <p className="mt-4 text-[0.95rem] leading-relaxed ug-muted">
          One decision, three people. Watch a problem found by HR get fixed by the CFO - and see the result flow back to HR without anyone sending an email.
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          <JumpButton view="overview" personaId="USR-MID-HR-003">🚀 Try Step 4: Open HR War Room (Priya)</JumpButton>
          <JumpButton view="overview" personaId="USR-UPPER-FIN-001">Approve Option B (CFO Arvind)</JumpButton>
        </div>
      </>
    ),
    right: (
      <Steps
        items={[
          <>Switch to <strong>Priya Kulkarni (HR Lead)</strong>.</>,
          <>Notice the warning alert: a schedule clash between the Finance payroll lock and the IT portal launch is <strong>blocking 142 families</strong>.</>,
          <>Switch to <strong>Arvind Mehta (CFO)</strong> to see the financial impact (<strong>₹38.4L</strong> premium change).</>,
          <>Click <strong>Approve Option B</strong> to use company funds and clear the blockage in one click.</>,
          <>Switch back to <strong>Priya (HR)</strong> and watch the warning turn into a <strong>green success badge</strong> automatically.</>,
        ]}
      />
    ),
  },
  {
    title: "You're ready",
    left: (
      <>
        <StepBadge n="All done" icon={BookOpen} />
        <Heading>You&apos;re ready to explore</Heading>
        <p className="mt-4 text-[0.95rem] leading-relaxed ug-muted">
          That&apos;s the whole journey: pick a role, talk to your documents, hit a security guardrail, and resolve a cross-team crisis.
        </p>
      </>
    ),
    right: (
      <>
        <p className="font-mono text-xs uppercase tracking-[0.25em] ug-muted">Jump back in</p>
        <div className="mt-4 flex flex-wrap gap-2.5">
          <JumpButton view="overview">Overview</JumpButton>
          <JumpButton view="documents">Documents</JumpButton>
          <JumpButton view="talk">Talk to Docs</JumpButton>
          <JumpButton view="benchmark">Open UI Benchmark</JumpButton>
        </div>
      </>
    ),
  },
]

const Half = ({ side, children }: { side: 'left' | 'right'; children: ReactNode }) => (
  <div className={cn('ug-half', side === 'left' ? 'ug-half-left' : 'ug-half-right')}>
    <div className="ug-content">{children}</div>
  </div>
)

export default function UserGuidePage() {
  const [index, setIndex] = useState(0)
  const [turn, setTurn] = useState<{ dir: 1 | -1; target: number } | null>(null)

  const go = useCallback(
    (dir: 1 | -1) => {
      if (turn) return
      const target = index + dir
      if (target < 0 || target >= SPREADS.length) return
      setTurn({ dir, target })
    },
    [index, turn],
  )

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') go(-1)
      if (e.key === 'ArrowRight') go(1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go])

  const cur = SPREADS[index]
  const tgt = turn ? SPREADS[turn.target] : null
  const reverse = turn?.dir === -1

  // Pages sitting underneath the turning leaf.
  const baseLeft = turn ? (reverse ? tgt!.left : cur.left) : cur.left
  const baseRight = turn ? (reverse ? cur.right : tgt!.right) : cur.right

  return (
    <div className="ug-root space-y-4">
      <div className="px-1">
        <h1 className="text-3xl font-semibold tracking-tight">User Guide</h1>
        <p className="mt-1 text-sm text-muted-foreground">Your 3-minute tour of StrataIQ. Turn the pages to follow the journey.</p>
      </div>

      <div className="ug-stage">
        <button className="ug-arrow prev" onClick={() => go(-1)} disabled={index === 0 || !!turn} aria-label="Previous page">
          <ChevronLeft className="size-9" strokeWidth={1} />
        </button>

        <div className="ug-book" role="group" aria-roledescription="book" aria-label={turn ? `Turning to ${tgt!.title}` : `User guide: ${cur.title}`}>
          <div className="ug-spread">
            <Half side="left">{baseLeft}</Half>
            <Half side="right">{baseRight}</Half>
            <span className="ug-gutter" aria-hidden="true" />

            {turn && (
              <div
                className={cn('ug-leaf turning', reverse && 'reverse')}
                aria-hidden="true"
                onAnimationEnd={() => {
                  setIndex(turn.target)
                  setTurn(null)
                }}
              >
                <div className="ug-face ug-face-front">
                  <div className="ug-content">{reverse ? cur.left : cur.right}</div>
                </div>
                <div className="ug-face ug-face-back">
                  <div className="ug-content">{reverse ? tgt!.right : tgt!.left}</div>
                </div>
              </div>
            )}
          </div>
        </div>

        <button className="ug-arrow next" onClick={() => go(1)} disabled={index === SPREADS.length - 1 || !!turn} aria-label="Next page">
          <ChevronRight className="size-9" strokeWidth={1} />
        </button>
      </div>

      <div className="flex flex-col items-center gap-2" aria-live="polite">
        <span className="font-mono text-xs uppercase tracking-[0.25em] text-muted-foreground">{cur.title}</span>
        <div className="flex items-center gap-2">
          {SPREADS.map((s, i) => (
            <span key={s.title} className={cn('h-1.5 rounded-full transition-all', i === index ? 'w-6 bg-primary' : 'w-1.5 bg-muted-foreground/30')} />
          ))}
          <span className="ml-2 font-mono text-[0.7rem] text-muted-foreground">
            {String(index + 1).padStart(2, '0')} / {String(SPREADS.length).padStart(2, '0')}
          </span>
        </div>
      </div>
    </div>
  )
}
