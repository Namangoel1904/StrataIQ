import { useEffect, useRef, type RefObject } from 'react'
import { cn } from '@/lib/utils'
import type { VoiceState } from './useVoice'

interface VoiceWaveProps {
  state: VoiceState
  /** Live 0..1 amplitude written by useVoice each frame. */
  levelRef: RefObject<number>
  className?: string
}

const STRANDS = [
  { hue: 222, w: 1.7, k: 2.1, sp: 1.4, ph: 0, amp: 1 },
  { hue: 232, w: 1.2, k: 2.9, sp: -1.1, ph: 1.3, amp: 0.8 },
  { hue: 214, w: 2.4, k: 1.6, sp: 0.8, ph: 2.6, amp: 0.95 },
  { hue: 248, w: 1.1, k: 3.6, sp: -1.7, ph: 4.1, amp: 0.6 },
  { hue: 205, w: 1.4, k: 2.4, sp: 1.9, ph: 5.2, amp: 0.72 },
]

/**
 * A subtle lens-shaped ribbon of light (see the "Voice interaction effect" reference):
 * strands pinch to a point at both ends, swell in the middle, and breathe with the voice level.
 */
export default function VoiceWave({ state, levelRef, className }: VoiceWaveProps) {
  const ref = useRef<HTMLCanvasElement>(null)
  const stateRef = useRef(state)
  stateRef.current = state

  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return
    let w = 0
    let h = 0
    let dpr = 1
    const resize = () => {
      const r = canvas.getBoundingClientRect()
      dpr = Math.min(2, devicePixelRatio || 1)
      w = r.width
      h = r.height
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
    let raf = 0
    let amp = 0.06
    const t0 = performance.now()

    const frame = (now: number) => {
      const t = (now - t0) / 1000
      const s = stateRef.current
      const live = levelRef.current ?? 0
      const target = s === 'idle' ? 0.07 + 0.025 * Math.sin(t * 1.3) : 0.16 + live * 0.95
      amp += (target - amp) * 0.12
      const speaking = s === 'speaking'

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)
      ctx.globalCompositeOperation = 'lighter'

      const cy = h / 2
      const pad = w * 0.04
      const span = w - pad * 2

      // central bloom
      const bloom = ctx.createRadialGradient(w / 2, cy, 0, w / 2, cy, span * 0.42)
      bloom.addColorStop(0, `hsla(${speaking ? 200 : 224},95%,62%,${0.1 + amp * 0.34})`)
      bloom.addColorStop(1, 'hsla(225,95%,60%,0)')
      ctx.fillStyle = bloom
      ctx.fillRect(0, 0, w, h)

      for (const [i, st] of STRANDS.entries()) {
        const hue = speaking ? st.hue - 22 : st.hue
        const g = ctx.createLinearGradient(pad, 0, w - pad, 0)
        g.addColorStop(0, `hsla(${hue},95%,70%,0)`)
        g.addColorStop(0.22, `hsla(${hue},95%,68%,0.55)`)
        g.addColorStop(0.5, `hsla(${hue + 10},100%,88%,0.95)`)
        g.addColorStop(0.78, `hsla(${hue},95%,68%,0.55)`)
        g.addColorStop(1, `hsla(${hue},95%,70%,0)`)
        ctx.strokeStyle = g
        ctx.lineWidth = st.w
        ctx.shadowColor = `hsla(${hue},100%,65%,0.8)`
        ctx.shadowBlur = 9
        ctx.beginPath()
        const N = 90
        for (let n = 0; n <= N; n++) {
          const u = n / N
          const env = Math.pow(Math.sin(Math.PI * u), 1.5)
          const wob = Math.sin(u * Math.PI * 2 * st.k + t * st.sp * (reduce ? 0 : 1) + st.ph)
          // strands fan out symmetrically either side of the centre line, like the reference lens
          const side = i % 2 === 0 ? 1 : -1
          const y = cy + side * env * (h * 0.42) * amp * st.amp * (0.45 + 0.55 * Math.abs(wob)) * (wob < 0 ? 0.6 : 1)
          const x = pad + u * span
          if (n === 0) ctx.moveTo(x, y)
          else ctx.lineTo(x, y)
        }
        ctx.stroke()
      }
      ctx.shadowBlur = 0

      // the hairline every strand converges onto
      const core = ctx.createLinearGradient(pad, 0, w - pad, 0)
      core.addColorStop(0, 'rgba(120,150,255,0)')
      core.addColorStop(0.5, `rgba(190,210,255,${0.55 + amp * 0.4})`)
      core.addColorStop(1, 'rgba(120,150,255,0)')
      ctx.fillStyle = core
      ctx.fillRect(pad, cy - 0.5, span, 1)
      ctx.globalCompositeOperation = 'source-over'

      raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)
    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
    }
  }, [levelRef])

  return (
    <div
      className={cn('relative overflow-hidden rounded-2xl bg-[radial-gradient(120%_140%_at_50%_50%,#0c1022_0%,#06070d_70%)]', className)}
      role="img"
      aria-label={state === 'listening' ? 'Listening' : state === 'speaking' ? 'Speaking' : 'Voice idle'}
    >
      <canvas ref={ref} className="block h-full w-full" />
      <span className="pointer-events-none absolute left-3 top-2 font-mono text-[0.62rem] uppercase tracking-[0.2em] text-sky-200/60">
        {state === 'listening' ? 'Listening' : state === 'speaking' ? 'Speaking' : 'Voice ready'}
      </span>
    </div>
  )
}
