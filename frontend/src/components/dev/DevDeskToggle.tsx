import { useEffect, useId, useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { Mic } from 'lucide-react'
import { useSession } from '@/state/session'

/**
 * Floating "developer at their desk" launcher. The sprite is the supplied pixel-art PNG; the
 * monitor's code is typed live over its screen quad and the two hands tap on the keyboard.
 * Clicking it opens the Talk-to-Documents studio.
 *
 * Coordinates below are in the sprite's original 1254² pixel space (viewBox crops to the art).
 */
const SCREEN = { a: 288, b: 142, c: 0, d: 198, e: 552, f: 185 } // unit square → screen parallelogram
const HAND_L = '468,538 473,533 492,521 496,521 530,526 542,544 542,556 524,563 486,570 484,570 479,564 468,552'
const HAND_R = '576,626 577,619 581,606 586,602 597,591 610,585 616,585 618,586 632,596 633,597 647,615 645,617 636,624 605,650 603,651 576,629'

const ROWS = 11
const COLORS = ['#f6c453', '#fbe9a6', '#9fd27c', '#f4934a', '#ffffff', '#8fd3ee']

// deterministic pseudo-random "code": [indent, length, colour] per row
const CODE = Array.from({ length: ROWS * 2 }, (_, i) => {
  const r = (n: number) => ((Math.sin(i * 12.9898 + n * 78.233) * 43758.5453) % 1 + 1) % 1
  return { indent: Math.floor(r(1) * 3) * 0.045, len: 0.14 + r(2) * 0.3, color: COLORS[Math.floor(r(3) * COLORS.length)] }
})

function useTypedCode() {
  const [tick, setTick] = useState(0)
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setTick(ROWS * 2 * 22)
      return
    }
    const id = setInterval(() => setTick((t) => t + 1), 55)
    return () => clearInterval(id)
  }, [])
  return tick
}

function Screen() {
  const tick = useTypedCode()
  const per = 22 // ticks per row
  const total = ROWS * 2 * per
  const cycle = tick % (total + 40)
  const rows: React.ReactNode[] = []
  for (let i = 0; i < ROWS * 2; i++) {
    const col = i < ROWS ? 0 : 1
    const row = i % ROWS
    const progress = Math.max(0, Math.min(1, (cycle - i * per) / per))
    if (progress <= 0) continue
    const { indent, len, color } = CODE[i]
    const x0 = (col === 0 ? 0.075 : 0.675) + indent
    const maxW = col === 0 ? 0.52 : 0.3
    const w = Math.min(len * (col === 0 ? 1.15 : 0.85), maxW - indent) * progress
    const y = 0.085 + row * 0.077
    rows.push(<rect key={i} x={x0} y={y} width={w} height={0.034} fill={color} opacity={0.92} />)
    if (progress < 1) {
      rows.push(<rect key={`c${i}`} x={x0 + w + 0.008} y={y - 0.006} width={0.016} height={0.046} fill="#fff" className="dev-caret" />)
    }
  }
  return (
    <g transform={`matrix(${SCREEN.a} ${SCREEN.b} ${SCREEN.c} ${SCREEN.d} ${SCREEN.e} ${SCREEN.f})`}>
      <rect x={0.045} y={0.055} width={0.945} height={0.87} fill="#4f9e98" />
      <rect x={0.628} y={0.055} width={0.012} height={0.87} fill="#3c817c" />
      {rows}
      <rect x={0.045} y={0.055} width={0.945} height={0.87} fill="#fff" className="dev-flicker" />
    </g>
  )
}

export default function DevDeskToggle() {
  const { go, catalog, view } = useSession()
  const uid = useId()
  const [hover, setHover] = useState(false)

  const lines = useMemo(() => {
    const t = catalog.data?.sample_voice_prompts.map((p) => p.spoken_text) ?? []
    return t.length ? t : ['Ask your documents anything…']
  }, [catalog.data])

  const [idx, setIdx] = useState(0)
  const [typed, setTyped] = useState(0)
  const full = lines[idx % lines.length]
  useEffect(() => {
    setTyped(0)
  }, [idx, lines])
  useEffect(() => {
    if (typed < full.length) {
      const t = setTimeout(() => setTyped((n) => n + 1), 34)
      return () => clearTimeout(t)
    }
    const t = setTimeout(() => setIdx((i) => (i + 1) % lines.length), 2600)
    return () => clearTimeout(t)
  }, [typed, full, lines.length])

  if (view === 'talk') return null

  return (
    <motion.button
      type="button"
      onClick={() => go('talk')}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      onFocus={() => setHover(true)}
      onBlur={() => setHover(false)}
      aria-label="Talk with your documents"
      className="group fixed bottom-3 right-3 z-40 flex flex-col items-end gap-1 bg-transparent p-0 text-left sm:bottom-5 sm:right-6"
      initial={{ opacity: 0, y: 60, scale: 0.85 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: 'spring', stiffness: 160, damping: 18, delay: 1.1 }}
      whileTap={{ scale: 0.97 }}
    >
      {/* chat bubble */}
      <div className={`glass relative mr-2 max-w-[14rem] rounded-2xl rounded-br-md px-3 py-2 shadow-xl transition-opacity duration-300 ${hover ? 'opacity-100' : 'opacity-80'}`}>
        <div className="mb-1 flex items-center gap-1.5 text-[0.66rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          <Mic className="size-3" />
          {hover ? 'Open voice studio' : 'Talk with your docs'}
        </div>
        <p className="caret min-h-[2.1rem] text-[0.76rem] leading-snug text-foreground">{full.slice(0, typed)}</p>
      </div>

      {/* sprite */}
      <div className="relative -mt-1 transition-transform duration-300 group-hover:-translate-y-1 group-hover:scale-[1.04]">
        <div className="absolute inset-x-6 bottom-1 h-6 rounded-[50%] bg-black/25 blur-xl" />
        <div className="absolute inset-x-10 bottom-4 h-24 rounded-full bg-[radial-gradient(closest-side,rgba(255,170,60,0.38),transparent)] blur-md" />
        <svg
          viewBox="51 148 1168 962"
          className="relative w-[10.5rem] sm:w-[14rem]"
          style={{ imageRendering: 'pixelated', filter: 'drop-shadow(0 10px 14px rgba(0,0,0,0.35))' }}
          role="img"
          aria-hidden="true"
        >
          <defs>
            <clipPath id={`${uid}-l`}>
              <polygon points={HAND_L} />
            </clipPath>
            <clipPath id={`${uid}-r`}>
              <polygon points={HAND_R} />
            </clipPath>
          </defs>
          <image href="/sprites/dev-desk.webp" x="51" y="148" width="1168" height="962" />
          <Screen />
          <g clipPath={`url(#${uid}-l)`}>
            <g className="dev-hand dev-hand-l">
              <image href="/sprites/dev-desk.webp" x="51" y="148" width="1168" height="962" />
            </g>
          </g>
          <g clipPath={`url(#${uid}-r)`}>
            <g className="dev-hand dev-hand-r">
              <image href="/sprites/dev-desk.webp" x="51" y="148" width="1168" height="962" />
            </g>
          </g>
        </svg>
      </div>
    </motion.button>
  )
}
