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

export interface SurveyPayload {
  ort_score: number
  budget_max?: number | null
  city?: string | null
  language?: Language | null
  answers: Record<string, unknown>
  tag_ids: number[]
}

export interface SurveySubmitResult {
  message: string
  submission: { id: number; user_id: number; ort_score: number; budget_max: number | null; city: string | null; language: string | null; answers: Record<string, unknown> }
  universities_top: UniversityTop[]
}

export interface UniversityTop {
  university: { id: number; name: string }
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