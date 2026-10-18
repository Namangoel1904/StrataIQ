import { useId } from 'react'

type HairStyle = 'side' | 'long' | 'bob' | 'short' | 'messy' | 'bun'

interface Look {
  skin: string
  hair: string
  style: HairStyle
  shirt: string
  accent?: string
  bg: [string, string]
  glasses?: boolean
  stubble?: boolean
  earrings?: boolean
}

// Showcase personas get hand-tuned looks; any other user id falls back to a hashed look.
const LOOKS: Record<string, Look> = {
  'USR-UPPER-FIN-001': { skin: '#d9a07a', hair: '#5b5d66', style: 'side', shirt: '#1f2a44', accent: '#7d9bde', bg: ['#d3dbf6', '#8fa6e6'], stubble: true },
  'USR-UPPER-HR-002': { skin: '#c98f6b', hair: '#1d1512', style: 'long', shirt: '#a8434f', bg: ['#f7dada', '#e79a9a'], earrings: true },
  'USR-MID-HR-003': { skin: '#e0a982', hair: '#2a1a14', style: 'bob', shirt: '#2f7a6c', bg: ['#d6f0e8', '#8fd1b8'] },
  'USR-MID-IT-004': { skin: '#c98d68', hair: '#17120f', style: 'short', shirt: '#4b4f63', bg: ['#e3def8', '#a99be4'], glasses: true },
  'USR-LOW-ENG-005': { skin: '#deaa84', hair: '#2b1b14', style: 'messy', shirt: '#2d5db3', bg: ['#ffe9c8', '#f2b25b'] },
  'USR-LOW-OPS-006': { skin: '#d29a74', hair: '#1c1411', style: 'bun', shirt: '#d98a2b', bg: ['#fde3ef', '#ee9cc4'], earrings: true },
}

const SKINS = ['#e0b08c', '#d29a74', '#c98d68', '#b87d58']
const HAIRS = ['#17120f', '#2b1b14', '#3a2a20', '#5b5d66']
const SHIRTS = ['#2d5db3', '#3b7a6e', '#a8434f', '#4b4f63', '#d98a2b']
const BGS: [string, string][] = [
  ['#d3dbf6', '#8fa6e6'],
  ['#d6f0e8', '#8fd1b8'],
  ['#fde3ef', '#ee9cc4'],
  ['#ffe9c8', '#f2b25b'],
]
const STYLES: HairStyle[] = ['short', 'side', 'bob', 'messy', 'bun', 'long']

function fallbackLook(id: string): Look {
  let h = 0
  for (const ch of id) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  return {
    skin: SKINS[h % SKINS.length],
    hair: HAIRS[(h >> 3) % HAIRS.length],
    style: STYLES[(h >> 5) % STYLES.length],
    shirt: SHIRTS[(h >> 7) % SHIRTS.length],
    bg: BGS[(h >> 9) % BGS.length],
    glasses: (h >> 11) % 3 === 0,
  }
}

function darken(hex: string, amt: number): string {
  const n = parseInt(hex.slice(1), 16)
  const f = (v: number) => Math.max(0, Math.min(255, Math.round(v * (1 - amt))))
  return `#${[(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => f(v).toString(16).padStart(2, '0')).join('')}`
}

interface AvatarProps {
  userId: string
  name?: string
  size?: number
  className?: string
}

export default function Avatar({ userId, name, size = 56, className }: AvatarProps) {
  const look = LOOKS[userId] ?? fallbackLook(userId)
  const gid = useId()
  const skinShade = darken(look.skin, 0.12)

  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={className}
      role="img"
      aria-label={name ? `Portrait of ${name}` : 'Portrait'}
    >
      <defs>
        <linearGradient id={`${gid}-bg`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={look.bg[0]} />
          <stop offset="1" stopColor={look.bg[1]} />
        </linearGradient>
        <clipPath id={`${gid}-clip`}>
          <circle cx="50" cy="50" r="50" />
        </clipPath>
      </defs>
      <g clipPath={`url(#${gid}-clip)`}>
        <rect width="100" height="100" fill={`url(#${gid}-bg)`} />

        {/* back hair */}
        {look.style === 'long' && <path d="M28 48C25 20 42 14 50 14s25 6 22 34l3 34H25l3-34Z" fill={look.hair} />}
        {look.style === 'bob' && <path d="M29 50C27 22 42 15 50 15s23 7 21 35l-2 18c-6 3-32 3-38 0l-2-18Z" fill={look.hair} />}

        {/* torso */}
        <path d="M10 104C10 82 28 73 50 73s40 9 40 31Z" fill={look.shirt} />
        {look.accent && <path d="M50 75l-4 8 4 14 4-14-4-8Z" fill={look.accent} />}
        {look.accent && <path d="M43 73l7 6 7-6-7-2-7 2Z" fill="#fff" opacity="0.92" />}
        {!look.accent && <path d="M40 73c3 6 17 6 20 0-4-2-16-2-20 0Z" fill={darken(look.shirt, 0.25)} />}

        {/* neck */}
        <path d="M43 62h14v13c-4 4-10 4-14 0V62Z" fill={skinShade} />

        {/* ears */}
        <circle cx="32.5" cy="48" r="3.4" fill={look.skin} />
        <circle cx="67.5" cy="48" r="3.4" fill={look.skin} />
        {look.earrings && (
          <>
            <circle cx="32.5" cy="53" r="1.6" fill="#f3c969" />
            <circle cx="67.5" cy="53" r="1.6" fill="#f3c969" />
          </>
        )}

        {/* head */}
        <ellipse cx="50" cy="46" rx="17.5" ry="20" fill={look.skin} />
        {look.stubble && <path d="M34 52c2 12 8 16 16 16s14-4 16-16c-3 6-9 9-16 9s-13-3-16-9Z" fill="#3b3d44" opacity="0.28" />}

        {/* front hair */}
        {look.style === 'short' && <path d="M31.5 45C29 26 41 19 50 19s21 7 18.5 26c-2-7-6-12-18.5-12S33.5 38 31.5 45Z" fill={look.hair} />}
        {look.style === 'side' && <path d="M31.5 46C28 25 42 18 52 19c11 1 17 9 16.5 27-1-8-5-13-12-14-8 1-18 2-25.5 14Z" fill={look.hair} />}
        {look.style === 'messy' && (
          <path d="M31 46c-3-14 1-23 10-26l2-4 4 3 4-4 3 4 5-1-1 4c7 3 10 11 8 24-1-8-4-13-10-14-6 1-15 1-25 14Z" fill={look.hair} />
        )}
        {look.style === 'bun' && (
          <>
            <circle cx="50" cy="15" r="7.5" fill={look.hair} />
            <path d="M31.5 46C29 27 41 20 50 20s21 7 18.5 26c-2-8-8-13-18.5-13S33.5 38 31.5 46Z" fill={look.hair} />
          </>
        )}
        {(look.style === 'long' || look.style === 'bob') && (
          <path d="M31 48C29 27 41 19 50 19s21 8 19 29c-3-10-9-15-19-15s-16 5-19 15Z" fill={look.hair} />
        )}

        {/* face */}
        <ellipse cx="43" cy="48" rx="1.9" ry="2.3" fill="#1b1620" />
        <ellipse cx="57" cy="48" rx="1.9" ry="2.3" fill="#1b1620" />
        <path d="M39.5 43.6q3.5-2 7 0M53.5 43.6q3.5-2 7 0" stroke={darken(look.hair, 0.1)} strokeWidth="1.6" strokeLinecap="round" fill="none" />
        <path d="M45 57.5q5 4 10 0" stroke="#7a3d33" strokeWidth="1.7" strokeLinecap="round" fill="none" />
        <ellipse cx="38" cy="54" rx="3.2" ry="2" fill="#e8806f" opacity="0.18" />
        <ellipse cx="62" cy="54" rx="3.2" ry="2" fill="#e8806f" opacity="0.18" />
        {look.glasses && (
          <g fill="none" stroke="#1b1620" strokeWidth="1.5">
            <rect x="36" y="43.5" width="12" height="9" rx="3.5" />
            <rect x="52" y="43.5" width="12" height="9" rx="3.5" />
            <path d="M48 47.5h4" />
          </g>
        )}
      </g>
    </svg>
  )
}
