import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'
import type { TalkToDocsResponse } from '@/lib/types'

export type VoiceState = 'idle' | 'listening' | 'speaking'

// Minimal typings for the (still vendor-prefixed) Web Speech recognition API.
interface RecognitionResultItem {
  isFinal: boolean
  0: { transcript: string }
}
interface RecognitionEvent {
  resultIndex: number
  results: ArrayLike<RecognitionResultItem>
}
interface Recognition {
  lang: string
  interimResults: boolean
  continuous: boolean
  onresult: ((e: RecognitionEvent) => void) | null
  onerror: ((e: { error: string }) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}
type RecognitionCtor = new () => Recognition
const getRecognition = (): RecognitionCtor | undefined => {
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor }
  return w.SpeechRecognition ?? w.webkitSpeechRecognition
}

const toBase64 = (blob: Blob) =>
  new Promise<string>((resolve, reject) => {
    const r = new FileReader()
    r.onload = () => resolve(String(r.result).split(',')[1] ?? '')
    r.onerror = () => reject(r.error)
    r.readAsDataURL(blob)
  })

interface Options {
  /** Called with the final transcript once the user stops speaking. */
  onFinal: (text: string) => void
  lang?: string
}

/**
 * Mic capture + speech playback. `levelRef` is a live 0..1 amplitude that the wave effect reads
 * every frame (a ref, not state, so the canvas can animate at 60fps without re-rendering React).
 */
export function useVoice({ onFinal, lang = 'en-IN' }: Options) {
  const [state, setState] = useState<VoiceState>('idle')
  const [interim, setInterim] = useState('')
  const [error, setError] = useState<string | null>(null)
  const levelRef = useRef(0)

  const onFinalRef = useRef(onFinal)
  onFinalRef.current = onFinal
  const stateRef = useRef<VoiceState>('idle')
  const setBoth = (s: VoiceState) => {
    stateRef.current = s
    setState(s)
  }

  const ctxRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const micNodes = useRef<{ stream?: MediaStream; src?: MediaStreamAudioSourceNode }>({})
  const recRef = useRef<Recognition | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const boostRef = useRef(0)
  const rafRef = useRef(0)

  const pump = useCallback(() => {
    const an = analyserRef.current
    let target = 0
    if (an) {
      const buf = new Uint8Array(an.fftSize)
      an.getByteTimeDomainData(buf)
      let sum = 0
      for (const v of buf) sum += ((v - 128) / 128) ** 2
      target = Math.min(1, Math.sqrt(sum / buf.length) * 3.2)
    } else if (stateRef.current === 'speaking') {
      // speechSynthesis can't be tapped for audio: synthesise a speech-like envelope instead
      const t = performance.now() / 1000
      boostRef.current *= 0.9
      target = Math.min(1, 0.28 + 0.22 * Math.abs(Math.sin(t * 7.3) * Math.sin(t * 2.1)) + boostRef.current * 0.4)
    }
    levelRef.current += (target - levelRef.current) * 0.28
    if (stateRef.current !== 'idle' || levelRef.current > 0.01) rafRef.current = requestAnimationFrame(pump)
    else levelRef.current = 0
  }, [])

  const ensureCtx = async () => {
    const ctx = (ctxRef.current ??= new AudioContext())
    if (ctx.state === 'suspended') await ctx.resume()
    return ctx
  }

  const releaseMic = useCallback(() => {
    micNodes.current.stream?.getTracks().forEach((t) => t.stop())
    micNodes.current.src?.disconnect()
    micNodes.current = {}
    if (!audioRef.current) analyserRef.current = null
  }, [])

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis?.cancel()
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
      analyserRef.current = null
    }
    if (stateRef.current === 'speaking') setBoth('idle')
  }, [])

  const startListening = useCallback(async () => {
    stopSpeaking()
    setError(null)
    setInterim('')
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    } catch {
      setError('Microphone access was blocked. Allow it in the browser to talk to your documents.')
      return
    }
    const ctx = await ensureCtx()
    const src = ctx.createMediaStreamSource(stream)
    const an = ctx.createAnalyser()
    an.fftSize = 512
    src.connect(an)
    analyserRef.current = an
    micNodes.current = { stream, src }

    const finish = (text?: string) => {
      releaseMic()
      recRef.current = null
      recorderRef.current = null
      setBoth('idle')
      setInterim('')
      if (text?.trim()) onFinalRef.current(text.trim())
    }

    const SR = getRecognition()
    if (SR) {
      const rec = new SR()
      rec.lang = lang
      rec.interimResults = true
      rec.continuous = false
      let finalText = ''
      rec.onresult = (e) => {
        let live = ''
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const r = e.results[i]
          if (r.isFinal) finalText += r[0].transcript
          else live += r[0].transcript
        }
        setInterim(finalText + live)
      }
      rec.onerror = (e) => {
        if (e.error !== 'no-speech' && e.error !== 'aborted') setError(`Speech recognition: ${e.error}`)
      }
      rec.onend = () => finish(finalText)
      recRef.current = rec
      rec.start()
    } else {
      // No browser STT (e.g. Firefox): record and let the backend transcribe.
      const chunks: Blob[] = []
      const mr = new MediaRecorder(stream)
      mr.ondataavailable = (e) => e.data.size && chunks.push(e.data)
      mr.onstop = async () => {
        releaseMic()
        setBoth('idle')
        try {
          const b64 = await toBase64(new Blob(chunks, { type: mr.mimeType }))
          const res = await api.transcribe({ audio_base64: b64, language_code: lang })
          finish(res.transcription)
        } catch {
          setError('Could not transcribe that recording.')
        }
      }
      recorderRef.current = mr
      mr.start()
    }

    setBoth('listening')
    cancelAnimationFrame(rafRef.current)
    rafRef.current = requestAnimationFrame(pump)
  }, [lang, pump, releaseMic, stopSpeaking])

  const stopListening = useCallback(() => {
    recRef.current?.stop()
    if (recorderRef.current && recorderRef.current.state !== 'inactive') recorderRef.current.stop()
  }, [])

  const speak = useCallback(
    async (res: TalkToDocsResponse, speed = 1) => {
      stopSpeaking()
      const synthOnly = /fallback/i.test(res.tts_engine || '') || /webspeech/i.test(res.voice_name || '') || !res.audio_base64
      cancelAnimationFrame(rafRef.current)
      if (synthOnly && 'speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(res.spoken_answer)
        u.lang = res.language_code || lang
        u.rate = speed
        const v = speechSynthesis.getVoices().find((x) => x.lang === u.lang) ?? speechSynthesis.getVoices().find((x) => x.lang.startsWith('en'))
        if (v) u.voice = v
        u.onboundary = () => (boostRef.current = 1)
        u.onend = u.onerror = () => {
          if (stateRef.current === 'speaking') setBoth('idle')
        }
        analyserRef.current = null
        setBoth('speaking')
        speechSynthesis.speak(u)
      } else {
        const audio = new Audio(`data:${res.audio_content_type};base64,${res.audio_base64}`)
        audio.playbackRate = speed
        const ctx = await ensureCtx()
        const node = ctx.createMediaElementSource(audio)
        const an = ctx.createAnalyser()
        an.fftSize = 512
        node.connect(an)
        an.connect(ctx.destination)
        analyserRef.current = an
        audioRef.current = audio
        audio.onended = () => {
          audioRef.current = null
          analyserRef.current = null
          setBoth('idle')
        }
        setBoth('speaking')
        await audio.play().catch(() => setBoth('idle'))
      }
      rafRef.current = requestAnimationFrame(pump)
    },
    [lang, pump, stopSpeaking],
  )

  useEffect(
    () => () => {
      cancelAnimationFrame(rafRef.current)
      recRef.current?.abort()
      releaseMic()
      window.speechSynthesis?.cancel()
      audioRef.current?.pause()
      void ctxRef.current?.close()
    },
    [releaseMic],
  )

  return { state, interim, error, levelRef, startListening, stopListening, speak, stopSpeaking, sttSupported: !!getRecognition() }
}
