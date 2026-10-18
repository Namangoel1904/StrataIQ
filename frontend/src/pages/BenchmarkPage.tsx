import { useState } from 'react'
import { Zap } from 'lucide-react'
import { api } from '@/lib/api'
import type { OpenUIBenchmark } from '@/lib/types'
import { cn } from '@/lib/utils'
import { Chip, Panel, PanelHeader, Stat } from '@/components/overview/primitives'

const DEFAULT_QUERY = 'Is Sahyadri Hospital in Pune cashless for cataract surgery under NovaShield?'

export default function BenchmarkPage() {
  const [query, setQuery] = useState(DEFAULT_QUERY)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<OpenUIBenchmark | null>(null)
  const [tab, setTab] = useState<'openui' | 'legacy'>('openui')

  const run = async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await api.benchmarkOpenUI(query))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Benchmark failed')
    } finally {
      setLoading(false)
    }
  }

  const pct = data ? (data.openui_tokens / Math.max(1, data.legacy_tokens)) * 100 : 0

  return (
    <div className="space-y-5">
      <Panel>
        <PanelHeader title="Thesys OpenUI vs. Legacy JSON Benchmark Lab" right={<Chip tone="green">Live</Chip>} />
        <div className="space-y-4 px-6 pb-6 pt-2 sm:px-8">
          <p className="text-sm text-muted-foreground">Live measurement of generative UI token reduction and latency throughput.</p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="min-w-0 flex-1 rounded-full bg-muted px-5 py-2.5 text-sm outline-none"
              aria-label="Benchmark query"
            />
            <button
              onClick={run}
              disabled={loading || !query.trim()}
              className="inline-flex items-center justify-center gap-2 rounded-full bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground disabled:opacity-50"
            >
              <Zap className="size-4" /> {loading ? 'Running Live Benchmark…' : 'Execute Live A/B Benchmark'}
            </button>
          </div>
          {error && <p className="text-sm text-coral">{error}</p>}
        </div>
      </Panel>

      {data && (
        <>
          <Panel>
            <div className="grid grid-cols-2 gap-6 p-6 sm:p-8 md:grid-cols-4">
              <Stat label="Token Reduction" value={`${data.token_reduction_pct}%`} sub="Fewer output tokens" tone="neutral" />
              <Stat label="Throughput Boost" value={`${data.speedup_multiplier}×`} sub="Faster output speed" />
              <Stat label="LLM Decode Saved" value={`~${(data.estimated_llm_decode_saved_ms / 1000).toFixed(1)}s`} sub="Decode latency cut" />
              <Stat label="Compute Overhead" value={`${data.openui_latency_ms} ms`} sub={`Legacy: ${data.legacy_latency_ms} ms`} />
            </div>
          </Panel>

          <Panel>
            <div className="space-y-3 p-6 sm:p-8">
              <div className="flex justify-between text-sm font-semibold">
                <span className="text-mint">Mode A: OpenUI ({data.openui_tokens} tokens)</span>
                <span className="text-coral">Mode B: Legacy JSON ({data.legacy_tokens} tokens)</span>
              </div>
              <div className="flex h-4 overflow-hidden rounded-full bg-muted">
                <div className="bg-mint transition-all duration-700" style={{ width: `${pct}%` }} />
                <div className="flex-1 bg-coral/60" />
              </div>
              <p className="text-xs text-muted-foreground">
                OpenUI delivers {data.token_reduction_pct}% token reduction and {data.speedup_multiplier}× faster structured output generation.
              </p>
            </div>
          </Panel>

          <Panel>
            <div className="space-y-3 p-6 sm:p-8">
              <div className="flex gap-2">
                {(['openui', 'legacy'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={cn(
                      'rounded-full px-4 py-1.5 text-xs font-semibold',
                      tab === t ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground',
                    )}
                  >
                    {t === 'openui' ? 'Mode A: openui-lang Output' : 'Mode B: Verbose JSON Output'}
                  </button>
                ))}
              </div>
              <pre className="max-h-72 overflow-auto rounded-2xl bg-muted p-4 font-mono text-xs">
                {tab === 'openui' ? data.openui_lang_code : JSON.stringify(data.legacy_verbose_payload, null, 2)}
              </pre>
            </div>
          </Panel>
        </>
      )}
    </div>
  )
}
