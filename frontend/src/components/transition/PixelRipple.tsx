import { useEffect, useRef } from 'react'

interface PixelRippleProps {
  origin: { x: number; y: number }
  onDone: () => void
}

const CELL = 34
const COVER_MS = 950 // time for the wavefront to reach the farthest corner
const FLASH_MS = 170 // coloured "pixel front" lifetime per cell
const HOLD_MS = 330 // how long a cell stays opaque before dissolving
const FADE_MS = 240

const FLASH = ['#dbe3f8', '#bccaf3', '#9db3ec', '#7d9bde', '#4285f4', '#eef1fb']
const GOOGLE = ['#ea4335', '#fbbc05', '#34a853']

/**
 * Radial, pixel-quantised reveal. Phase per cell: wave arrives → coloured flash → opaque paper
 * (hides the hero) → dissolves to reveal the dashboard mounted underneath.
 */
export default function PixelRipple({ origin, onDone }: PixelRippleProps) {
  const ref = useRef<HTMLCanvasElement>(null)
  const doneRef = useRef(onDone)
  doneRef.current = onDone

  useEffect(() => {
    const canvas = ref.current
    const ctx = canvas?.getContext('2d')
    if (!canvas || !ctx) return

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      doneRef.current()
      return
    }

    const w = window.innerWidth
    const h = window.innerHeight
    canvas.width = w
    canvas.height = h
    const cols = Math.ceil(w / CELL)
    const rows = Math.ceil(h / CELL)
    const maxD = Math.max(
      Math.hypot(origin.x, origin.y),
      Math.hypot(w - origin.x, origin.y),
      Math.hypot(origin.x, h - origin.y),
      Math.hypot(w - origin.x, h - origin.y),
    )

    const n = cols * rows
    const cover = new Float32Array(n)
    const fadeDelay = new Float32Array(n)
    const colour: string[] = new Array(n)
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const i = r * cols + c
        const d = Math.hypot(c * CELL + CELL / 2 - origin.x, r * CELL + CELL / 2 - origin.y)
        cover[i] = (d / maxD) * COVER_MS + Math.random() * 90
        fadeDelay[i] = Math.random() * 130
        colour[i] = Math.random() < 0.07 ? GOOGLE[(Math.random() * 3) | 0] : FLASH[(Math.random() * FLASH.length) | 0]
      }
    }
    const total = COVER_MS + 90 + HOLD_MS + 130 + FADE_MS + 40

    let raf = 0
    const t0 = performance.now()
    const frame = (now: number) => {
      const t = now - t0
      ctx.clearRect(0, 0, w, h)
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const i = r * cols + c
          const local = t - cover[i]
          if (local < 0) continue
          let alpha = 1
          let fill = '#ffffff'
          if (local < FLASH_MS) {
            fill = colour[i]
          } else if (local > HOLD_MS + fadeDelay[i]) {
            alpha = 1 - (local - HOLD_MS - fadeDelay[i]) / FADE_MS
            if (alpha <= 0) continue
            // pixels shrink toward their centre as they dissolve
            const k = CELL * (0.35 + 0.65 * alpha)
            ctx.globalAlpha = alpha
            ctx.fillStyle = fill
            ctx.fillRect(c * CELL + (CELL - k) / 2, r * CELL + (CELL - k) / 2, k, k)
            continue
          }
          ctx.globalAlpha = alpha
          ctx.fillStyle = fill
          ctx.fillRect(c * CELL, r * CELL, CELL + 0.5, CELL + 0.5)
        }
      }
      ctx.globalAlpha = 1
      if (t < total) raf = requestAnimationFrame(frame)
      else doneRef.current()
    }
    raf = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(raf)
    // origin is fixed for the lifetime of one ripple
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return <canvas ref={ref} className="pointer-events-none fixed inset-0 z-[70]" aria-hidden="true" />
}
