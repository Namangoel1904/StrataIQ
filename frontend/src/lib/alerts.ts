import type { BootstrapResponse, LowerKPIs, MiddleKPIs, UpperKPIs } from './types'

export interface AlertItem {
  id: string
  title: string
  detail: string
  tone: 'critical' | 'warning' | 'info'
}

export function deriveAlerts(boot: BootstrapResponse | null | undefined): AlertItem[] {
  if (!boot) return []
  const alerts: AlertItem[] = []
  const user = boot.user_profile
  const k = boot.role_scoped_kpis

  if (user.layer_code === 'UPPER') {
    const u = k as UpperKPIs
    if (u.pending_executive_decisions > 0) {
      alerts.push({
        id: 'upper-decision-pending',
        title: 'Parental Premium Variance (DEC-2026-001)',
        detail: 'Executive Option B pending sign-off to allocate ₹19.2L refund and extend payroll cutoff to Oct 25.',
        tone: 'critical',
      })
    }
  } else if (user.layer_code === 'MIDDLE') {
    const m = k as MiddleKPIs
    if (m.conflict_alert) {
      alerts.push({
        id: 'middle-collision',
        title: 'Schedule Collision: TSK-03 vs TSK-05',
        detail: `${m.employees_blocked_parental_rider || 142} employees blocked due to Finance payroll lock preceding IT SSO portal launch.`,
        tone: 'critical',
      })
    }
    if (m.stuck_transition_claims_count > 0) {
      alerts.push({
        id: 'middle-claims-stuck',
        title: `${m.stuck_transition_claims_count} Transition Claims in Audit`,
        detail: 'Hospital claims requiring TPA portal and discharge summary verification.',
        tone: 'warning',
      })
    }
  } else if (user.layer_code === 'LOWER') {
    const l = k as LowerKPIs
    if (l.enrollment?.parental_opt_in === 'PENDING_CONFIRMATION') {
      alerts.push({
        id: 'lower-optin-pending',
        title: 'Parental Rider Confirmation Needed',
        detail: 'Confirm before Oct 22 to guarantee cashless cataract and hospital admission for your parents.',
        tone: 'critical',
      })
    }
  }

  return alerts
}
