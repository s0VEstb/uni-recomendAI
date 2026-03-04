const API_BASE = '/api'

function getToken(): string | null {
  return localStorage.getItem('token')
}

export async function api<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken()
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    // Если токен протух или пользователь удалён — очищаем локальное состояние и отправляем на логин
    if (res.status === 401) {
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(Array.isArray(err.detail) ? err.detail[0]?.msg ?? res.statusText : err.detail ?? res.statusText)
  }
  return res.json()
}

export const auth = {
  register: (email: string, password: string) =>
    api<{ access_token: string; token_type: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    api<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  forgotPassword: (email: string) =>
    api<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    }),
  resetPassword: (token: string, newPassword: string) =>
    api<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    }),
}

export type TagType = 'interest' | 'strength' | 'subject' | 'career'

export interface Tag {
  id: number
  slug: string
  title: string
  type: TagType
  is_active: boolean
}

export function listTags(tagType?: TagType): Promise<Tag[]> {
  const q = tagType ? `?tag_type=${tagType}` : ''
  return api<Tag[]>(`/tags${q}`)
}

export type Language = 'russian' | 'kyrgyz' | 'english' | 'turkish'

export type City = 'bishkek' | 'osh' | 'jalal_abad' | 'karakol' | 'tokmok' | 'naryn' | 'batken' | 'talas' | 'uzgen' | 'kara_balta' | 'balykchy' | 'bazar_korgon' | 'kyzyl_kiya' | 'tash_kumyr' | 'kant' | 'isfana' | 'mailuu_suu' | 'kara_suu' | 'other'

export interface SurveyPayload {
  ort_score: number
  budget_max?: number | null
  city?: City | null
  language?: Language | null
  notes?: string | null
  needs_dorm?: boolean | null
  willing_to_relocate?: boolean | null
  answers: Record<string, unknown>
  tag_ids: number[]
}

export interface SurveySubmissionData {
  id: number
  user_id: number
  ort_score: number
  budget_max: number | null
  city: string | null
  language: string | null
  notes: string | null
  needs_dorm: boolean | null
  willing_to_relocate: boolean | null
  answers: Record<string, unknown>
  tag_ids?: number[]
}

export interface SurveySubmitResult {
  message: string
  submission: SurveySubmissionData
  universities_top: UniversityTop[]
}

export interface UniversityTop {
  university: { id: number; name: string; photo_url?: string | null }
  score: number
  programs_count: number
  programs: ProgramRecommendation[]
}

export interface ProgramRecommendation {
  program: { id: number; name: string }
  university: { id: number; name: string }
  score: number
  reasons: { code: string; message: string; meta: Record<string, unknown> }[]
}

export function submitSurvey(payload: SurveyPayload): Promise<SurveySubmitResult> {
  return api<SurveySubmitResult>('/survey/submit', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getLatestSurvey(): Promise<SurveySubmitResult> {
  return api<SurveySubmitResult>('/survey/latest')
}

export interface ProgramDetail {
  id: number
  name: string
  language: string
  study_form: string
  duration_years: number
  official_url: string | null
  university: {
    id: number
    name: string
    city: string
    website: string
    photo_url: string | null
  }
  fees: { id: number; name: string; year: number; contract_fee: number; currency: string }[]
  admissions: { id: number; year: number; ort_min_score: number | null; requirements: Record<string, unknown>; deadlines: Record<string, unknown> }[]
  tags: { id: number; slug: string; title: string }[]
}

export function getProgramDetail(universityId: number, programId: number): Promise<ProgramDetail> {
  return api<ProgramDetail>(`/universities/${universityId}/programs/${programId}`)
}

export function getProgramById(programId: number): Promise<ProgramDetail> {
  return api<ProgramDetail>(`/programs/${programId}`)
}

export interface CompareResponse {
  programs: ProgramDetail[]
}

export function comparePrograms(programIds: number[]): Promise<CompareResponse> {
  return api<CompareResponse>('/compare/', {
    method: 'POST',
    body: JSON.stringify({ program_ids: programIds }),
  })
}

export interface ChatStreamCallbacks {
  onMetadata?: (meta: { sources: unknown[]; found: boolean }) => void
  onChunk?: (text: string) => void
  onDone?: () => void
  onError?: (err: Error) => void
}

export async function chatStream(
  question: string,
  options?: { university_id?: number; program_id?: number; top_k?: number },
  callbacks?: ChatStreamCallbacks
): Promise<void> {
  const token = localStorage.getItem('token')
  const res = await fetch('/api/chat/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      question,
      university_id: options?.university_id ?? null,
      program_id: options?.program_id ?? null,
      top_k: options?.top_k ?? 4,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    callbacks?.onError?.(new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail)))
    return
  }
  const reader = res.body?.getReader()
  if (!reader) {
    callbacks?.onError?.(new Error('No response body'))
    return
  }
  const decoder = new TextDecoder()
  let buffer = ''
  let metadataDone = false
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk
      if (!metadataDone && buffer.includes('--METADATA_END--')) {
        const idx = buffer.indexOf('--METADATA_END--')
        const metaStr = buffer.slice(0, idx).trim()
        metadataDone = true
        try {
          const meta = JSON.parse(metaStr)
          callbacks?.onMetadata?.(meta)
        } catch {
          /* ignore */
        }
        const afterMeta = buffer.slice(idx + '--METADATA_END--\n'.length)
        if (afterMeta) callbacks?.onChunk?.(afterMeta)
        buffer = ''
      } else if (metadataDone && chunk) {
        callbacks?.onChunk?.(chunk)
      }
    }
    if (metadataDone && buffer) callbacks?.onChunk?.(buffer)
    callbacks?.onDone?.()
  } catch (e) {
    callbacks?.onError?.(e instanceof Error ? e : new Error(String(e)))
  }
}

// ═══════════════════════════════════════════════
// Chat History API (server-side, JWT-authenticated)
// ═══════════════════════════════════════════════

export interface ChatSessionData {
  id: number
  title: string
  university_id: number | null
  program_id: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ChatMessageData {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface ChatSessionDetail extends ChatSessionData {
  messages: ChatMessageData[]
}

export const chatHistory = {
  list: (): Promise<{ sessions: ChatSessionData[] }> =>
    api<{ sessions: ChatSessionData[] }>('/chat/sessions'),

  create: (data: { title?: string; university_id?: number | null; program_id?: number | null }): Promise<ChatSessionData> =>
    api<ChatSessionData>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  get: (id: number): Promise<ChatSessionDetail> =>
    api<ChatSessionDetail>(`/chat/sessions/${id}`),

  delete: (id: number): Promise<{ ok: boolean }> =>
    api<{ ok: boolean }>(`/chat/sessions/${id}`, { method: 'DELETE' }),

  rename: (id: number, title: string): Promise<ChatSessionData> =>
    api<ChatSessionData>(`/chat/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    }),

  addMessage: (sessionId: number, role: string, content: string): Promise<ChatMessageData> =>
    api<ChatMessageData>(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ role, content }),
    }),
}
