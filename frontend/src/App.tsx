import { useCallback, useEffect, useState } from 'react'
import { AnimatePresence } from 'motion/react'
import { api } from '@/lib/api'
import { SessionProvider, useSession } from '@/state/session'
import Loader from '@/components/loader/Loader'
import Hero from '@/components/hero/Hero'
import PixelRipple from '@/components/transition/PixelRipple'
import Shell from '@/components/shell/Shell'
import OverviewPage from '@/pages/OverviewPage'
import DocumentsPage from '@/pages/DocumentsPage'
import TalkPage from '@/pages/TalkPage'

type Phase = 'loading' | 'hero' | 'rippling' | 'app'

const preload = (src: string) =>
  new Promise<void>((resolve) => {
    const img = new Image()
    img.onload = img.onerror = () => resolve()
    img.src = src
  })

function Root() {
  const { boot, setPersonas, theme, view } = useSession()
  const [phase, setPhase] = useState<Phase>('loading')
  const [origin, setOrigin] = useState({ x: 0, y: 0 })
  const [assetsReady, setAssetsReady] = useState(false)

  // Real readiness: fonts, the launcher sprite, and the persona list from the API.
  useEffect(() => {
    void Promise.all([
      document.fonts.ready,
      preload('/sprites/dev-desk.webp'),
      api
        .personas()
        .then((r) => setPersonas(r.personas))
        .catch(() => undefined),
    ]).then(() => setAssetsReady(true))
  }, [setPersonas])

  // The loader + hero are always light; the stored theme applies from the ripple onward.
  useEffect(() => {
    const dark = theme === 'dark' && (phase === 'rippling' || phase === 'app')
    document.documentElement.classList.toggle('dark', dark)
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', dark ? '#090a0f' : '#ffffff')
  }, [theme, phase])

  const onLoaded = useCallback(() => setPhase('hero'), [])
  const initialize = useCallback((o: { x: number; y: number }) => {
    setOrigin(o)
    setPhase('rippling')
  }, [])
  const onRippled = useCallback(() => setPhase('app'), [])

  const dashboardMounted = phase === 'rippling' || phase === 'app'

  return (
    <>
      {dashboardMounted && (
        <Shell>
          {view === 'overview' && <OverviewPage />}
          {view === 'documents' && <DocumentsPage />}
          {view === 'talk' && <TalkPage />}
        </Shell>
      )}

      {phase !== 'app' && (
        <div className="fixed inset-0 z-[45]">
          <Hero active={phase !== 'loading'} leaving={phase === 'rippling'} onInitialize={initialize} />
        </div>
      )}

      <AnimatePresence>{phase === 'loading' && <Loader ready={assetsReady && !boot.loading} onDone={onLoaded} />}</AnimatePresence>
      {phase === 'rippling' && <PixelRipple origin={origin} onDone={onRippled} />}
    </>
  )
}

export default function App() {
  return (
    <SessionProvider>
      <Root />
    </SessionProvider>
  )
}
