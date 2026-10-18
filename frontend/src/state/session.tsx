import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api, DEFAULT_USER, setApiUser } from '@/lib/api'
import { useAsync, type AsyncState } from '@/lib/hooks'
import type { BootstrapResponse, DocumentsListResponse, UserContext, VoiceCatalogResponse } from '@/lib/types'

export type View = 'overview' | 'documents' | 'talk'
export type Theme = 'light' | 'dark'
export interface PendingAsk {
  query: string
  docIds: string[]
}

interface Session {
  personas: UserContext[]
  setPersonas: (p: UserContext[]) => void
  userId: string
  switchPersona: (id: string) => void
  boot: AsyncState<BootstrapResponse>
  docs: AsyncState<DocumentsListResponse>
  catalog: AsyncState<VoiceCatalogResponse>
  view: View
  go: (v: View) => void
  /** A question (and documents to point at) handed from Overview to the Talk studio. */
  pending: PendingAsk | null
  ask: (query: string, docIds?: string[]) => void
  clearPending: () => void
  theme: Theme
  toggleTheme: () => void
}

const Ctx = createContext<Session | null>(null)

const read = (k: string): string | null => {
  try {
    return localStorage.getItem(k)
  } catch {
    return null
  }
}
const write = (k: string, v: string) => {
  try {
    localStorage.setItem(k, v)
  } catch {
    /* storage unavailable (private mode) */
  }
}

const VIEWS: View[] = ['overview', 'documents', 'talk']
const viewFromHash = (): View => {
  const h = window.location.hash.replace('#/', '')
  return (VIEWS as string[]).includes(h) ? (h as View) : 'overview'
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [personas, setPersonas] = useState<UserContext[]>([])
  const [userId, setUserId] = useState<string>(() => read('strataiq.user') ?? DEFAULT_USER)
  const [theme, setTheme] = useState<Theme>(() => (read('strataiq.theme') === 'dark' ? 'dark' : 'light'))
  const [view, setView] = useState<View>(viewFromHash)
  const [pending, setPending] = useState<PendingAsk | null>(null)

  // Keep the API header in lock-step with the selected persona *before* children fetch.
  setApiUser(userId)

  const boot = useAsync(() => api.bootstrap(), [userId])
  const docs = useAsync(() => api.documents(), [userId])
  const catalog = useAsync(() => api.voiceCatalog(), [userId])

  const switchPersona = useCallback((id: string) => {
    setApiUser(id)
    setUserId(id)
    write('strataiq.user', id)
  }, [])

  const go = useCallback((v: View) => {
    setView(v)
    window.history.replaceState(null, '', `#/${v}`)
    window.scrollTo({ top: 0 })
  }, [])

  const ask = useCallback(
    (query: string, docIds: string[] = []) => {
      setPending({ query, docIds })
      go('talk')
    },
    [go],
  )
  const clearPending = useCallback(() => setPending(null), [])

  useEffect(() => {
    const onHash = () => setView(viewFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])

  const toggleTheme = useCallback(() => {
    setTheme((t) => {
      const next = t === 'dark' ? 'light' : 'dark'
      write('strataiq.theme', next)
      return next
    })
  }, [])

  const value = useMemo<Session>(
    () => ({ personas, setPersonas, userId, switchPersona, boot, docs, catalog, view, go, pending, ask, clearPending, theme, toggleTheme }),
    [personas, userId, switchPersona, boot, docs, catalog, view, go, pending, ask, clearPending, theme, toggleTheme],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useSession(): Session {
  const v = useContext(Ctx)
  if (!v) throw new Error('useSession must be used inside <SessionProvider>')
  return v
}
