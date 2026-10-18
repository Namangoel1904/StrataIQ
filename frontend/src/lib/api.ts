import type {
  UserContext,
  BootstrapResponse,
  DocumentsListResponse,
  DocumentContentResponse,
  VoiceCatalogResponse,
  TalkToDocsResponse,
  DecisionMatrixItem,
  OpenUIBenchmark,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export const DEFAULT_USER = 'USR-LOW-ENG-005'

let currentUserId = DEFAULT_USER

export function setApiUser(userId: string): void {
  currentUserId = userId
}

function headers(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-User-Id': currentUserId,
  }
}

export const api = {
  getUserId(): string {
    return currentUserId
  },

  downloadUrl(docId: string): string {
    return `${API_BASE}/api/v1/documents/${encodeURIComponent(docId)}/download`
  },

  async personas(): Promise<{ total_personas: number; personas: UserContext[] }> {
    const res = await fetch(`${API_BASE}/api/v1/workspace/personas`)
    if (!res.ok) throw new Error(`Failed to fetch personas: ${res.statusText}`)
    return res.json()
  },

  async bootstrap(userId?: string): Promise<BootstrapResponse> {
    const uid = userId || currentUserId
    const res = await fetch(`${API_BASE}/api/v1/workspace/bootstrap`, {
      headers: { ...headers(), 'X-User-Id': uid },
    })
    if (!res.ok) throw new Error(`Bootstrap failed (${res.status}): ${res.statusText}`)
    return res.json()
  },

  async documents(userId?: string): Promise<DocumentsListResponse> {
    const uid = userId || currentUserId
    const res = await fetch(`${API_BASE}/api/v1/documents`, {
      headers: { ...headers(), 'X-User-Id': uid },
    })
    if (!res.ok) throw new Error(`Failed to fetch documents: ${res.statusText}`)
    return res.json()
  },

  async documentContent(docId: string): Promise<DocumentContentResponse> {
    const res = await fetch(`${API_BASE}/api/v1/documents/${encodeURIComponent(docId)}/content`, {
      headers: headers(),
    })
    if (!res.ok) throw new Error(`Failed to fetch document content: ${res.statusText}`)
    return res.json()
  },

  async decisions(): Promise<{ total_decisions: number; decisions: DecisionMatrixItem[] }> {
    const res = await fetch(`${API_BASE}/api/v1/decisions`, {
      headers: headers(),
    })
    if (!res.ok) throw new Error(`Failed to fetch decisions: ${res.statusText}`)
    const data = await res.json()
    // Backend returns an array directly or { total_decisions, decisions }
    if (Array.isArray(data)) {
      return { total_decisions: data.length, decisions: data }
    }
    return data
  },

  async approveDecision(
    decisionId: string,
    selectedOption: string,
    executiveNotes?: string
  ): Promise<any> {
    const res = await fetch(
      `${API_BASE}/api/v1/decisions/${encodeURIComponent(decisionId)}/approve`,
      {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({
          selected_option: selectedOption,
          executive_notes: executiveNotes || 'Approved via StrataIQ Executive Matrix',
        }),
      }
    )
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Approval failed with status ${res.status}`)
    }
    return res.json()
  },

  async confirmRider(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/api/v1/workspace/confirm-parental-rider`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        opt_in_choice: 'CONFIRMED',
      }),
    })
    if (!res.ok) throw new Error(`Confirm rider failed: ${res.statusText}`)
    return res.json()
  },

  async resetDemo(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/workspace/reset-demo-state`, {
      method: 'POST',
      headers: headers(),
    })
    if (!res.ok) throw new Error(`Reset demo failed: ${res.statusText}`)
    return res.json()
  },

  async voiceCatalog(userId?: string): Promise<VoiceCatalogResponse> {
    const uid = userId || currentUserId
    const res = await fetch(`${API_BASE}/api/v1/voice/catalog`, {
      headers: { ...headers(), 'X-User-Id': uid },
    })
    if (!res.ok) throw new Error(`Failed to fetch voice catalog: ${res.statusText}`)
    return res.json()
  },

  async talkToDocs(payload: {
    query: string
    pointed_doc_ids?: string[]
    language_code?: string
    voice_speed?: number
  }): Promise<TalkToDocsResponse> {
    const res = await fetch(`${API_BASE}/api/v1/voice/talk-to-docs`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        query: payload.query,
        pointed_doc_ids: payload.pointed_doc_ids || [],
        language_code: payload.language_code || 'en-IN',
        voice_speed: payload.voice_speed || 1.0,
      }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || `Talk to docs failed with status ${res.status}`)
    }
    return res.json()
  },

  async transcribe(payload: {
    audio_base64: string
    language_code?: string
  }): Promise<{ transcription: string }> {
    const res = await fetch(`${API_BASE}/api/v1/voice/transcribe`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        audio_base64: payload.audio_base64,
        language_code: payload.language_code || 'en-IN',
      }),
    })
    if (!res.ok) throw new Error(`Transcription failed: ${res.statusText}`)
    return res.json()
  },

  async benchmarkOpenUI(query: string, docHints?: string[]): Promise<OpenUIBenchmark> {
    const res = await fetch(`${API_BASE}/api/v1/agent/benchmark-openui`, {
      method: 'POST',
      headers: headers(),
      body: JSON.stringify({
        query,
        doc_hints: docHints || [],
      }),
    })
    if (!res.ok) throw new Error(`Benchmark failed: ${res.statusText}`)
    return res.json()
  },
}
