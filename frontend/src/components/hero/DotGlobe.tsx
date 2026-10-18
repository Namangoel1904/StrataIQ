import { useEffect, useRef } from 'react'
import { ARCS, REGIONS, buildLandDots } from './world'

const DEG = Math.PI / 180
const TILT = 22 * DEG

type V3 = [number, number, number]
const toVec = (lat: number, lon: number): V3 => [
  Math.cos(lat * DEG) * Math.cos(lon * DEG),
  Math.cos(lat * DEG) * Math.sin(lon * DEG),
  Math.sin(lat * DEG),
]

/** Rotate a world vector into view space → [screenX, screenY(up), depth]. */
function view(v: V3, lon0: number): V3 {
  const l = lon0 * DEG
  const x = v[0] * Math.cos(l) + v[1] * Math.sin(l)
  const y = -v[0] * Math.sin(l) + v[1] * Math.cos(l)
  const z = v[2]
  return [y, z * Math.cos(TILT) - x * Math.sin(TILT), x * Math.cos(TILT) + z * Math.sin(TILT)]
}

function slerp(a: V3, b: V3, t: number, lift: number): V3 {
  const dot = Math.min(1, Math.max(-1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]))
  const th = Math.acos(dot) || 1e-6
  const s = Math.sin(th)
  const k1 = Math.sin((1 - t) * th) / s
  const k2 = Math.sin(t * th) / s
  const h = 1 + lift * Math.sin(Math.PI * t)
  return [(a[0] * k1 + b[0] * k2) * h, (a[1] * k1 + b[1] * k2) * h, (a[2] * k1 + b[2] * k2) * h]
}

const smooth = (a: number, b: number, x: number) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}

/** Slowly turning dot-matrix globe with Google Cloud region nodes and animated routes. */
export default function DotGlobe({ className }: { className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const land = buildLandDots().map(([lon, lat]) => toVec(lat, lon))
    const regionVec = new Map(REGIONS.map((r) => [r.id, toVec(r.lat, r.lon)]))
    const arcs = ARCS.map(([a, b], i) => {
      const va = regionVec.get(a)!
      const vb = regionVec.get(b)!
      const ang = Math.acos(Math.min(1, Math.max(-1, va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2])))
      return { va, vb, lift: 0.07 + 0.2 * (ang / Math.PI), phase: (i * 0.173) % 1, speed: 0.07 + (i % 4) * 0.012 }
    })

    let w = 0
    let h = 0
    let dpr = 1
    const resize = () => {
      const r = canvas.getBoundingClientRect()
      dpr = Math.min(2, window.devicePixelRatio || 1)
      w = r.width
      h = r.height
      canvas.width = Math.round(w * dpr)
      canvas.height = Math.round(h * dpr)
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let raf = 0
    const t0 = performance.now()

    const frame = (now: number) => {
      const t = (now - t0) / 1000
      const lon0 = -36 + (reduce ? 0 : t * 2.4)
      const R = Math.min(w * 0.42, h * 0.8)
      const cx = w / 2
      const cy = h * 0.6
      const s = Math.min(1.25, Math.max(0.7, R / 560))
      const P = (v: V3): [number, number] => [cx + v[0] * R, cy - v[1] * R]

      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)

      // sphere body
      const g = ctx.createRadialGradient(cx - R * 0.28, cy - R * 0.38, R * 0.08, cx, cy, R)
      g.addColorStop(0, '#fbfbfc')
      g.addColorStop(0.7, '#eeeff1')
      g.addColorStop(1, '#e2e3e7')
      ctx.beginPath()
      ctx.arc(cx, cy, R, 0, Math.PI * 2)
      ctx.fillStyle = g
      ctx.fill()
      ctx.strokeStyle = 'rgba(20,24,40,0.05)'
      ctx.lineWidth = 1
      ctx.stroke()

      // land dots
      for (const v of land) {
        const p = view(v, lon0)
        if (p[2] < 0.03) continue
        const [x, y] = P(p)
        const a = 0.25 + 0.6 * Math.sqrt(p[2])
        ctx.fillStyle = `rgba(150,154,166,${a})`
        ctx.beginPath()
        ctx.arc(x, y, (1.1 + 1.25 * p[2]) * s, 0, Math.PI * 2)
        ctx.fill()
      }

      // routes
      ctx.lineWidth = 1.1 * s
      for (const arc of arcs) {
        let prev: [number, number] | null = null
        ctx.beginPath()
        for (let i = 0; i <= 56; i++) {
          const p = view(slerp(arc.va, arc.vb, i / 56, arc.lift), lon0)
          if (p[2] < 0.02) {
            prev = null
            continue
          }
          const [x, y] = P(p)
          if (prev) ctx.lineTo(x, y)
          else ctx.moveTo(x, y)
          prev = [x, y]
        }
        ctx.strokeStyle = 'rgba(110,116,134,0.32)'
        ctx.stroke()

        // travelling pulse
        const u = (t * arc.speed + arc.phase) % 1
        const pp = view(slerp(arc.va, arc.vb, u, arc.lift), lon0)
        if (pp[2] > 0.02) {
          const [x, y] = P(pp)
          const halo = ctx.createRadialGradient(x, y, 0, x, y, 9 * s)
          halo.addColorStop(0, 'rgba(66,133,244,0.55)')
          halo.addColorStop(1, 'rgba(66,133,244,0)')
          ctx.fillStyle = halo
          ctx.beginPath()
          ctx.arc(x, y, 9 * s, 0, Math.PI * 2)
          ctx.fill()
          ctx.fillStyle = '#4285f4'
          ctx.beginPath()
          ctx.arc(x, y, 2.1 * s, 0, Math.PI * 2)
          ctx.fill()
        }
      }

      // nodes + labels
      ctx.textBaseline = 'middle'
      for (const r of REGIONS) {
        const p = view(regionVec.get(r.id)!, lon0)
        if (p[2] < 0.04) continue
        const [x, y] = P(p)
        const vis = smooth(0.05, 0.4, p[2])
        ctx.globalAlpha = vis

        if (r.accent) {
          const k = (t * 0.7) % 1
          ctx.beginPath()
          ctx.arc(x, y, (5 + k * 18) * s, 0, Math.PI * 2)
          ctx.strokeStyle = `rgba(66,133,244,${0.55 * (1 - k)})`
          ctx.lineWidth = 1.4 * s
          ctx.stroke()
        }

        ctx.fillStyle = r.accent ? '#4285f4' : '#34a853'
        ctx.beginPath()
        ctx.arc(x, y, (r.accent ? 4.2 : 3.2) * s, 0, Math.PI * 2)
        ctx.fill()

        const lx = x + r.dx * s
        const ly = y + r.dy * s
        ctx.strokeStyle = r.accent ? 'rgba(66,133,244,0.85)' : 'rgba(80,120,190,0.6)'
        ctx.lineWidth = 1.2 * s
        ctx.beginPath()
        ctx.moveTo(x, y)
        ctx.lineTo(lx, ly + 10 * s)
        ctx.stroke()

        const num = r.zones
        const nf = `700 ${14 * s}px "Manrope Variable", system-ui, sans-serif`
        const cf = `${r.accent ? 700 : 500} ${14 * s}px "Manrope Variable", system-ui, sans-serif`
        ctx.font = nf
        const nw = ctx.measureText(num).width
        ctx.fillStyle = '#4a86d8'
        ctx.fillText(num, lx - nw - 7 * s, ly)
        ctx.fillStyle = 'rgba(70,74,90,0.35)'
        ctx.fillRect(lx - 3.5 * s, ly - 9 * s, 1.2 * s, 18 * s)
        ctx.font = cf
        ctx.fillStyle = r.accent ? '#1f2230' : 'rgba(60,64,80,0.75)'
        ctx.fillText(r.city, lx + 5 * s, ly)
        ctx.globalAlpha = 1
      }

      raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)
    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
    }
  }, [])

  return <canvas ref={ref} className={className} aria-hidden="true" />
}
