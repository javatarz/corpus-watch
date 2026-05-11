const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? ''

export interface SetupStatus {
  configured: boolean
  household_name?: string
}

export interface SetupPayload {
  individual_name: string
  household_name: string
}

export interface NetWorth {
  total: string
  currency: string
  as_of: string | null
}

export interface ImportResult {
  imported: number
  skipped: number
  total: string
  currency: string
  as_of: string | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? `Request failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const getSetup = (): Promise<SetupStatus> =>
  request<SetupStatus>('/api/setup')

export const postSetup = (payload: SetupPayload): Promise<void> =>
  request<void>('/api/setup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

export const getNetworth = (): Promise<NetWorth> =>
  request<NetWorth>('/api/networth')

export async function importCas(file: File, password: string): Promise<ImportResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('password', password)
  const res = await fetch(`${BASE}/api/import/cas`, { method: 'POST', body: form })
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as { detail?: string }
    throw new Error(body.detail ?? `Import failed: ${res.status}`)
  }
  return res.json() as Promise<ImportResult>
}
