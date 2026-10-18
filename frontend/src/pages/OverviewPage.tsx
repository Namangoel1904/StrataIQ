import { motion } from 'motion/react'
import { WifiOff } from 'lucide-react'
import { firstName, greeting } from '@/lib/format'
import type { LowerKPIs, MiddleKPIs } from '@/lib/types'
import { useSession } from '@/state/session'
import { TextShimmer } from '@/components/ui/shimmer-text'
import PersonaStudio from '@/components/overview/PersonaStudio'
import { BenefitsPanel, ClaimsPanel, ConflictPanel, DecisionPanel, RecentQueries, RolePulse } from '@/components/overview/RoleModules'

export default function OverviewPage() {
  const { boot } = useSession()
  const data = boot.data
  const me = data?.user_profile
  const layer = me?.layer_code

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-1 pb-1 pt-1">
        <div>
          <h1 className="text-[clamp(2rem,4vw,2.9rem)] font-semibold leading-tight tracking-tight">
            {me ? `${greeting()}, ${firstName(me.full_name)}` : 'Welcome back'}
          </h1>
          <p className="mt-1 text-[0.95rem] text-muted-foreground">
            {me ? `${me.job_title} · ${me.dept_name}. Here is what needs you today.` : 'Loading your workspace…'}
          </p>
        </div>
        {boot.loading && data && <TextShimmer className="text-sm font-medium">Switching persona…</TextShimmer>}
      </div>

      {boot.error && (
        <div className="glass flex items-center gap-3 rounded-2xl px-5 py-4 text-sm" role="alert">
          <WifiOff className="size-5 text-coral" />
          <span>
            Can&apos;t reach the StrataIQ API ({boot.error}). Start the backend with <code className="font-mono">uvicorn app.main:app --port 8000</code>.
          </span>
          <button onClick={boot.reload} className="ml-auto rounded-full bg-primary px-4 py-1.5 text-xs font-semibold text-primary-foreground">
            Retry
          </button>
        </div>
      )}

      <PersonaStudio />

      {data && (
        <motion.div key={me?.user_id} className="space-y-5" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, ease: [0.2, 0.8, 0.2, 1] }}>
          <div className="grid gap-5 xl:grid-cols-12">
            <div className="xl:col-span-7">
              {layer === 'UPPER' && <DecisionPanel />}
              {layer === 'MIDDLE' && <ConflictPanel conflict={(data.role_scoped_kpis as MiddleKPIs).conflict_alert} />}
              {layer === 'LOWER' && <BenefitsPanel kpis={data.role_scoped_kpis as LowerKPIs} />}
            </div>
            <div className="xl:col-span-5">
              <RolePulse boot={data} />
            </div>
          </div>
          {layer === 'LOWER' && <ClaimsPanel claims={(data.role_scoped_kpis as LowerKPIs).personal_claims} />}
          <RecentQueries />
        </motion.div>
      )}
    </div>
  )
}
