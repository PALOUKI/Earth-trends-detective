export interface VariableInfo {
  id: string
  name: string
  name_fr: string
  unit: string
  definition: string
  definition_fr: string
  period: string
  limitations: string
  windows: string[]
}

export interface RegionInfo {
  id: string
  name: string
  name_fr: string
  bounds: [number, number, number, number]
  description: string
  description_fr: string
}

export interface TrendInfo {
  n_valid: number
  slope_ols: number | null
  slope_ols_lo: number | null
  slope_ols_hi: number | null
  p_ols: number | null
  slope: number | null
  slope_lo: number | null
  slope_hi: number | null
  p_mk: number | null
  p_value: number | null
}

export interface Analysis {
  variable: string
  label: string
  unit: string
  bounds?: Record<string, number>
  location?: { lat: number; lon: number }
  period: { start: string; end: string }
  time: string[]
  value: Array<number | null>
  seasonal: Array<number | null>
  anomaly: Array<number | null>
  trend: TrendInfo
  significant: boolean
  summary: { en: string; fr: string }
  caveats: string[]
}

export interface MapLayer {
  slope_unit: string
  scale_min: number
  scale_max: number
  minzoom: number
  maxzoom: number
  palette: { negative: string; zero: string; positive: string }
  urls: { slope: string; nonsignificant: string }
}

const apiBase = import.meta.env.VITE_API_BASE ?? ''

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export const api = {
  variables: () => getJson<VariableInfo[]>('/api/variables'),
  regions: () => getJson<RegionInfo[]>('/api/regions'),
  suggest: (theme: string, place: string) =>
    getJson<Array<{ variable: string; name: string; definition: string; available: boolean; message: string }>>(
      `/api/suggest?theme=${encodeURIComponent(theme)}&place=${encodeURIComponent(place)}`,
    ),
  region: (bounds: [number, number, number, number], label: string, start?: string, end?: string) =>
    postJson<Analysis>('/api/region', { variable: 'gistemp_tas_anom', bounds, label, start, end }),
  point: (lat: number, lon: number, start?: string, end?: string) =>
    getJson<Analysis>(`/api/point?variable=gistemp_tas_anom&lat=${lat}&lon=${lon}${start ? `&start=${start}` : ''}${end ? `&end=${end}` : ''}`),
  map: (window: string) => getJson<MapLayer>(`/api/trend/gistemp_tas_anom?window=${window}`),
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}
