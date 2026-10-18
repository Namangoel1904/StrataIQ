import { useEffect, useRef, useState } from 'react'
import { motion } from 'motion/react'
import { FileText } from 'lucide-react'

interface LoaderProps {
  /** True once real work (fonts, sprite, personas, workspace bootstrap) has finished. */
  ready: boolean
  onDone: () => void
}

const MIN_MS = 2600

const STEPS = [
  { at: 0, label: 'Establishing zero-trust context' },
  { at: 28, label: 'Loading role personas' },
  { at: 55, label: 'Indexing document vault' },
  { at: 82, label: 'Warming the agent engine' },
  { at: 100, label: 'Ready' },
]

export default function Loader({ ready, onDone }: LoaderProps) {
  const [progress, setProgress] = useState(0)
  const startedAt = useRef(performance.now())
  const readyRef = useRef(ready)
  readyRef.current = ready
  const doneRef = useRef(false)

  useEffect(() => {
    let raf = 0
    const tick = () => {
      const elapsed = performance.now() - startedAt.current
      const mayFinish = readyRef.current && elapsed > MIN_MS
      // Ease toward 88% on a timer; only the real "ready" signal unlocks the last 12%.
      const target = mayFinish ? 100 : Math.min(88, (elapsed / MIN_MS) * 88)
      setProgress((p) => {
        const next = p + (target - p) * 0.08
        return Math.abs(target - next) < 0.15 ? target : next
      })
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  useEffect(() => {
    if (progress >= 100 && !doneRef.current) {
      doneRef.current = true
      const t = setTimeout(onDone, 650)
      return () => clearTimeout(t)
    }
  }, [progress, onDone])

  const step = [...STEPS].reverse().find((s) => progress >= s.at) ?? STEPS[0]
  const pct = Math.round(progress)

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden"
      style={{ background: 'linear-gradient(180deg, #fdfdfd 0%, #e2e2e4 38%, #b4b4b7 72%, #8e8e92 100%)' }}
      initial={{ y: 0 }}
      exit={{ y: '-100%' }}
      transition={{ duration: 1, ease: [0.76, 0, 0.24, 1] }}
      role="status"
      aria-live="polite"
      aria-label={`Loading StrataIQ ${pct}%`}
    >
      {/* Frosted track the capsule rides in */}
      <div
        className="absolute inset-x-0 top-1/2 h-[7.5rem] -translate-y-1/2 border-y border-white/60"
        style={{
          background: 'linear-gradient(180deg, rgba(255,255,255,0.35), rgba(255,255,255,0.08))',
          backdropFilter: 'blur(6px)',
          boxShadow: '0 1px 0 rgba(255,255,255,0.7) inset',
        }}
      />

      <motion.div
        className="relative"
        initial={{ opacity: 0, scale: 0.9, y: 8 }}
        animate={{ opacity: 1, scale: progress >= 100 ? 1.06 : 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.2, 0.8, 0.2, 1] }}
      >
        {/* soft outer halo ring, as in the reference capsule */}
        <div className="absolute -inset-2.5 rounded-full border border-white/70 bg-white/20 shadow-[0_0_40px_rgba(255,255,255,0.6)]" />
        <div className="glass-capsule relative flex h-[4.6rem] min-w-[19rem] items-center gap-3.5 overflow-hidden rounded-full pl-7 pr-8">
          {/* progress wash inside the capsule */}
          <div
            className="pointer-events-none absolute inset-y-0 left-0 bg-gradient-to-r from-black/[0.03] to-black/[0.09]"
            style={{ width: `${progress}%` }}
          />
          <FileText className="relative size-7 text-neutral-500" strokeWidth={1.6} />
          <span className="relative font-sans text-[1.65rem] font-medium tracking-tight text-neutral-800">
            {progress >= 100 ? 'StrataIQ' : 'Initializing'}
          </span>
          <span className="relative ml-auto font-mono text-sm tabular-nums text-neutral-500">{pct}%</span>
        </div>
      </motion.div>

      <div className="absolute bottom-[22%] flex flex-col items-center gap-3">
        <p key={step.label} className="animate-in fade-in-0 slide-in-from-bottom-1 font-mono text-[0.8rem] uppercase tracking-[0.22em] text-neutral-700/80 duration-500">
          {step.label}
        </p>
        <div className="h-px w-48 overflow-hidden bg-neutral-900/15">
          <div className="h-full bg-neutral-900/70" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </motion.div>
  )
}
