import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowUp, BookOpenText, Mic, Sparkles, Square, Volume2, VolumeX } from 'lucide-react'
import { api } from '@/lib/api'
import { prettyDocName } from '@/lib/format'
import type { TalkToDocsResponse } from '@/lib/types'
import { cn } from '@/lib/utils'
import { useSession } from '@/state/session'
import { TextShimmer } from '@/components/ui/shimmer-text'
import { Chip, Panel, PanelHeader } from '@/components/overview/primitives'
import CitationViewer from '@/components/talk/CitationViewer'
import DocumentDeck from '@/components/talk/DocumentDeck'
import VoiceWave from '@/components/talk/VoiceWave'
import { useVoice } from '@/components/talk/useVoice'

interface Turn {
  id: number
  query: string
  pointed: string[]
  status: 'thinking' | 'done' | 'error'
  res?: TalkToDocsResponse
  error?: string
}

const THINKING = [
  'Agent is thinking ...',
  'Routing your question ...',
  'Searching pointed documents ...',
  'Checking your records ...',
  'Verifying every claim ...',
]

function Thinking() {
  const [i, setI] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % THINKING.length), 1400)
    return () => clearInterval(t)
  }, [])
  return (
    <div className="flex items-center gap-3 py-1" role="status" aria-live="polite">
      <Sparkles className="size-4 text-muted-foreground" />
      <TextShimmer className="font-light text-md tracking-tight">{THINKING[i]}</TextShimmer>
    </div>
  )
}

function Switch({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      role="switch"
      aria-checked={on}
      onClick={() => onChange(!on)}
      className="inline-flex items-center gap-2 text-xs font-medium text-muted-foreground hover:text-foreground"
    >
      <span className={cn('relative h-5 w-9 rounded-full transition-colors', on ? 'bg-primary' : 'bg-border')}>
        <span className={cn('absolute top-0.5 size-4 rounded-full bg-background transition-all', on ? 'left-[1.1rem]' : 'left-0.5')} />
      </span>
      {label}
    </button>
  )
}

export default function TalkPage() {
  const { boot, docs, catalog, pending, clearPending } = useSession()
  const me = boot.data?.user_profile
  const accessible = useMemo(() => docs.data?.accessible_docs ?? [], [docs.data])

  const [turns, setTurns] = useState<Turn[]>([])
  const [input, setInput] = useState('')
  const [pointed, setPointed] = useState<string[]>([])
  const [speakOn, setSpeakOn] = useState(true)
  const [focusId, setFocusId] = useState<number | null>(null)
  const idRef = useRef(0)
  const endRef = useRef<HTMLDivElement>(null)

  const speed = (me?.ui_preferences.voice_speed as number | undefined) ?? 1
  const busy = turns.some((t) => t.status === 'thinking')

  const runRef = useRef<(q: string, docIds?: string[]) => void>(() => {})
  const voice = useVoice({ onFinal: (text) => runRef.current(text) })

  const run = useCallback(
    async (q: string, docIds: string[] = pointed) => {
      const query = q.trim()
      if (!query) return
      voice.stopSpeaking()
      const id = ++idRef.current
      setTurns((t) => [...t, { id, query, pointed: docIds, status: 'thinking' }])
      setFocusId(id)
      setInput('')
      try {
        const res = await api.talkToDocs({ query, pointed_doc_ids: docIds, voice_speed: speed })
        setTurns((t) => t.map((x) => (x.id === id ? { ...x, status: 'done', res } : x)))
        if (speakOn) void voice.speak(res, speed)
      } catch (e) {
        setTurns((t) => t.map((x) => (x.id === id ? { ...x, status: 'error', error: e instanceof Error ? e.message : 'Something went wrong' } : x)))
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [pointed, speed, speakOn, voice.speak, voice.stopSpeaking],
  )
  runRef.current = run

  // A question handed over from the Overview page (prompt tiles, "Ask again", doc cards).
  const handledPendingRef = useRef<unknown>(null)
  useEffect(() => {
    if (!pending || !docs.data) return
    if (handledPendingRef.current === pending) return // StrictMode re-runs effects before clearPending lands
    handledPendingRef.current = pending
    const ids = pending.docIds.filter((id) => accessible.some((d) => d.doc_id === id))
    setPointed(ids)
    clearPending()
    void run(pending.query, ids)
  }, [pending, docs.data]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [turns])

  const toggle = (id: string) => setPointed((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]))
  const focus = turns.find((t) => t.id === focusId && t.res)?.res ?? [...turns].reverse().find((t) => t.res)?.res ?? null
  const listening = voice.state === 'listening'
  const prompts = catalog.data?.sample_voice_prompts ?? []

  return (
    <div className="space-y-5">
      <div className="pt-1">
        <h1 className="text-[clamp(2rem,4vw,2.9rem)] font-semibold leading-tight tracking-tight">Talk to your documents</h1>
        <p className="mt-1 text-[0.95rem] text-muted-foreground">
          Point at the documents that matter, then ask out loud. Every answer is grounded, cited and scoped to your clearance.
        </p>
      </div>

      <div className="grid items-start gap-5 xl:grid-cols-12">
        {/* ───────── left: composer + thread ───────── */}
        <div className="space-y-5 xl:col-span-7">
          <Panel className="p-5 sm:p-7">
            <p className="mb-3 text-sm text-muted-foreground">
              {pointed.length === 0 ? (
                'No document pointed yet. I will search everything you can access.'
              ) : (
                <>
                  Pointing at <span className="font-semibold text-foreground">{pointed.length}</span> document{pointed.length > 1 ? 's' : ''}:{' '}
                  {pointed.map((id) => prettyDocName(accessible.find((d) => d.doc_id === id)?.file_name ?? id)).join(', ')}
                </>
              )}
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault()
                void run(input)
              }}
              className="glass flex items-center gap-2 rounded-full py-2 pl-6 pr-2"
            >
              <input
                value={listening ? voice.interim : input}
                onChange={(e) => setInput(e.target.value)}
                readOnly={listening}
                placeholder={listening ? 'Listening…' : 'Ask anything about your documents…'}
                className="min-w-0 flex-1 bg-transparent py-2 text-[1rem] outline-none placeholder:text-muted-foreground"
                aria-label="Your question"
              />
              <div className="relative">
                {listening && <span className="absolute inset-0 rounded-full bg-sky/50 [animation:ring-ping_1.4s_ease-out_infinite]" />}
                <button
                  type="button"
                  onClick={() => (listening ? voice.stopListening() : void voice.startListening())}
                  aria-pressed={listening}
                  aria-label={listening ? 'Stop listening' : 'Speak your question'}
                  className={cn('round-btn relative !size-11', listening && '!bg-primary !text-primary-foreground')}
                >
                  {listening ? <Square className="size-4 fill-current" /> : <Mic className="size-5" strokeWidth={1.7} />}
                </button>
              </div>
              <button
                type="submit"
                disabled={busy || !input.trim()}
                aria-label="Send"
                className="grid size-11 place-items-center rounded-full bg-primary text-primary-foreground transition-opacity disabled:opacity-30"
              >
                <ArrowUp className="size-5" />
              </button>
            </form>

            <VoiceWave state={voice.state} levelRef={voice.levelRef} className="mt-4 h-[5.5rem]" />
            {voice.error && <p className="mt-2 text-xs text-coral">{voice.error}</p>}

            <div className="mt-4 flex flex-wrap items-center gap-2">
              {prompts.map((p) => (
                <button
                  key={p.prompt_id}
                  onClick={() => {
                    setPointed(p.pointed_doc_ids)
                    void run(p.spoken_text, p.pointed_doc_ids)
                  }}
                  disabled={busy}
                  title={p.spoken_text}
                  className="glass inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-transform hover:-translate-y-0.5 disabled:opacity-50"
                >
                  <Sparkles className="size-3.5 text-sky" />
                  {p.title}
                </button>
              ))}
              <div className="ml-auto">
                <Switch on={speakOn} onChange={(v) => { setSpeakOn(v); if (!v) voice.stopSpeaking() }} label="Speak answers" />
              </div>
            </div>
          </Panel>

          <Panel className="min-h-[14rem] p-5 sm:p-7">
            {turns.length === 0 ? (
              <div className="grid min-h-[11rem] place-items-center text-center">
                <div>
                  <p className="text-lg font-semibold">Your conversation starts here</p>
                  <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
                    Try a suggested question above, or tap the mic and speak. Answers are read aloud and the cited paragraph opens on the right.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <AnimatePresence initial={false}>
                  {turns.map((t) => (
                    <motion.div key={t.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }} className="space-y-3">
                      <div className="flex justify-end">
                        <p className="max-w-[85%] rounded-3xl rounded-br-lg bg-primary px-5 py-3 text-[0.95rem] text-primary-foreground">{t.query}</p>
                      </div>
                      <div className="flex gap-3">
                        <span className="mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-muted">
                          <Sparkles className="size-4" />
                        </span>
                        <div className="min-w-0 flex-1 rounded-3xl rounded-tl-lg border border-white/70 bg-card/80 px-5 py-4 dark:border-white/5 dark:bg-card/60">
                          {t.status === 'thinking' && <Thinking />}
                          {t.status === 'error' && <p className="text-sm text-coral">{t.error}</p>}
                          {t.res && (
                            <>
                              <p className="whitespace-pre-line text-[0.95rem] leading-relaxed">{t.res.display_answer}</p>
                              <div className="mt-4 flex flex-wrap items-center gap-2">
                                <Chip tone={t.res.is_grounded ? 'green' : 'amber'}>
                                  {t.res.is_grounded ? 'Grounded' : 'Low confidence'} · {Math.round(t.res.groundedness_score * 100)}%
                                </Chip>
                                <Chip>{Math.round(t.res.latency_breakdown_ms.total_ms ?? 0)} ms</Chip>
                                <button
                                  onClick={() => setFocusId(t.id)}
                                  className={cn(
                                    'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-colors',
                                    focusId === t.id ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground hover:bg-muted/70',
                                  )}
                                >
                                  <BookOpenText className="size-3.5" /> Sources ({t.res.citations.length})
                                </button>
                                <button
                                  onClick={() => (voice.state === 'speaking' ? voice.stopSpeaking() : void voice.speak(t.res!, speed))}
                                  className="ml-auto inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-semibold hover:bg-muted/70"
                                >
                                  {voice.state === 'speaking' ? <VolumeX className="size-3.5" /> : <Volume2 className="size-3.5" />}
                                  {voice.state === 'speaking' ? 'Stop' : 'Listen'}
                                </button>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                <div ref={endRef} />
              </div>
            )}
          </Panel>
        </div>

        {/* ───────── right: point a doc + source viewer ───────── */}
        <div className="space-y-5 xl:col-span-5">
          <Panel className="pb-5">
            <PanelHeader title="Point a doc" right={<Chip tone="blue">{accessible.length} accessible</Chip>} className="pb-4" />
            <div className="px-6 sm:px-8">
              {docs.loading && accessible.length === 0 ? (
                <p className="py-16 text-center text-sm text-muted-foreground">Loading vault…</p>
              ) : (
                <DocumentDeck docs={accessible} pointed={pointed} onToggle={toggle} onClear={() => setPointed([])} />
              )}
            </div>
          </Panel>

          <Panel className="pb-6">
            <PanelHeader title="Source viewer" className="pb-4" />
            <div className="px-6 sm:px-8">
              <CitationViewer primary={focus?.primary_citation ?? null} citations={focus?.citations ?? []} />
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}
