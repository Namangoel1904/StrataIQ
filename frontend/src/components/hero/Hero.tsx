import { useEffect, useRef } from 'react'
import { motion, type Variants } from 'motion/react'
import { ArrowUpRight } from 'lucide-react'
import DotGlobe from './DotGlobe'

interface HeroProps {
  /** Becomes true when the loader curtain has lifted; drives the entrance choreography. */
  active: boolean
  /** True while the pixel-ripple is consuming the hero. */
  leaving: boolean
  onInitialize: (origin: { x: number; y: number }) => void
}

const word: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.055, delayChildren: 0.15 } },
}
const letter: Variants = {
  hidden: { opacity: 0, y: 34, filter: 'blur(12px)' },
  show: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.8, ease: [0.2, 0.8, 0.2, 1] } },
}
const rise = (delay: number): Variants => ({
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.8, delay, ease: [0.2, 0.8, 0.2, 1] } },
})

function DocGlyph({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 76" className={className} aria-hidden="true">
      <path d="M8 6a6 6 0 0 1 6-6h26l20 20v50a6 6 0 0 1-6 6H14a6 6 0 0 1-6-6V6Z" fill="#0b0b0f" />
      <path d="M40 0v14a6 6 0 0 0 6 6h14L40 0Z" fill="#fff" />
      <rect x="2" y="38" width="46" height="26" rx="8" fill="#0b0b0f" stroke="#fff" strokeWidth="4" />
      <text x="25" y="57" textAnchor="middle" fontFamily="Manrope Variable, system-ui, sans-serif" fontWeight="600" fontSize="17" fill="#fff">
        DOC
      </text>
    </svg>
  )
}

function GoogleCloudMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 32" className={className} aria-hidden="true">
      <path d="M31 8.2 36.6 6A12 12 0 0 0 14.4 9.6l1.5 4.8 15.1-6.2Z" fill="#ea4335" />
      <path d="M38.2 11.2 31 8.2l-3 8 5.2 5.2h5.4A8 8 0 0 0 40 12.4l-1.8-1.2Z" fill="#4285f4" />
      <path d="M12.4 27h20.8l-5.2-5.2-9.6-.4L12.4 27Z" fill="#34a853" />
      <path d="M8.4 27h4l6-5.6L14.4 9.6A9.6 9.6 0 0 0 8.4 27Z" fill="#fbbc05" />
    </svg>
  )
}

export default function Hero({ active, leaving, onInitialize }: HeroProps) {
  const btn = useRef<HTMLButtonElement>(null)

  const fire = () => {
    const r = btn.current?.getBoundingClientRect()
    onInitialize(r ? { x: r.left + r.width / 2, y: r.top + r.height / 2 } : { x: innerWidth / 2, y: innerHeight / 2 })
  }

  useEffect(() => {
    if (!active || leaving) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Enter') fire()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  return (
    <div className="fixed inset-0 overflow-hidden bg-white text-[#0b0b0f]">
      <motion.div
        className="absolute inset-0"
        initial={{ opacity: 0, scale: 1.08 }}
        animate={active ? { opacity: leaving ? 0 : 1, scale: leaving ? 1.1 : 1 } : {}}
        transition={{ duration: leaving ? 0.7 : 1.6, ease: [0.2, 0.8, 0.2, 1] }}
      >
        <DotGlobe className="h-full w-full" />
      </motion.div>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_52%_46%_at_50%_50%,rgba(255,255,255,0.92),rgba(255,255,255,0)_70%)]" />

      <motion.div
        className="relative z-10 flex h-full flex-col items-center justify-center px-6 text-center"
        animate={leaving ? { opacity: 0, scale: 0.96, filter: 'blur(6px)' } : { opacity: 1, scale: 1, filter: 'blur(0px)' }}
        transition={{ duration: 0.5, ease: 'easeIn' }}
      >
        <motion.h1
          className="relative flex items-end font-serif font-semibold leading-none tracking-tight text-[clamp(4.2rem,13vw,10.5rem)]"
          variants={word}
          initial="hidden"
          animate={active ? 'show' : 'hidden'}
          aria-label="StrataIQ"
        >
          {'StrataI'.split('').map((c, i) => (
            <motion.span key={i} variants={letter} aria-hidden="true" className="inline-block">
              {c}
            </motion.span>
          ))}
          <motion.span variants={letter} aria-hidden="true" className="relative inline-block">
            Q
            <DocGlyph className="absolute -bottom-[0.02em] -right-[0.2em] h-[0.5em] w-[0.42em]" />
          </motion.span>
        </motion.h1>

        <motion.p
          className="mt-3 max-w-[52rem] text-[clamp(0.85rem,1.3vw,1.1rem)] font-light tracking-wide text-[#1d1f2a]"
          variants={rise(0.9)}
          initial="hidden"
          animate={active ? 'show' : 'hidden'}
        >
          The Role-Adaptive Enterprise Knowledge, Voice &amp; Decision Copilot
        </motion.p>

        <motion.div
          className="mt-5 flex items-center gap-3"
          variants={rise(1.05)}
          initial="hidden"
          animate={active ? 'show' : 'hidden'}
        >
          <span className="text-[0.72rem] font-extrabold uppercase tracking-[0.22em]">Powered by</span>
          <span className="flex items-center gap-1.5">
            <GoogleCloudMark className="h-6 w-9" />
            <span className="text-[1.35rem] font-medium tracking-tight text-[#5f6368]">Google Cloud</span>
          </span>
        </motion.div>

        <motion.div
          className="mt-[clamp(2.5rem,7vh,5rem)]"
          variants={rise(1.25)}
          initial="hidden"
          animate={active ? 'show' : 'hidden'}
        >
          <button ref={btn} type="button" className="cta-pill" onClick={fire} disabled={leaving} aria-label="Initialize StrataIQ">
            <span>Ease The Task</span>
            <ArrowUpRight className="size-7" strokeWidth={1.5} />
          </button>
        </motion.div>

        <motion.p
          className="absolute bottom-7 font-mono text-[0.68rem] uppercase tracking-[0.24em] text-neutral-400"
          variants={rise(1.7)}
          initial="hidden"
          animate={active ? 'show' : 'hidden'}
        >
          Zero-Trust RLS · 3 Layers × 6 Departments · Voice-native
        </motion.p>
      </motion.div>
    </div>
  )
}
