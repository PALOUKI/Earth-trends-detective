export interface VariableInfo {
  id: string
  name: string
  name_fr: string
  unit: string
  definition: string
  definition_fr: string
  period: string
  limitations: string
  windows?: string[]
  data_start?: string
  data_end?: string
  status?: 'analysis_ready' | 'sample_downloaded' | 'acquiring' | 'series_processed' | 'blocked_eula'
  status_detail?: string
  source?: string
  short_name?: string | null
  doi?: string
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
  rate_unit: string
  bounds?: Record<string, number>
  location?: { lat: number; lon: number }
  period: { start: string; end: string }
  time: string[]
  value: Array<number | null>
  seasonal: Array<number | null>
  anomaly: Array<number | null>
  trend: TrendInfo
  break?: { date: string; p: number; significant: boolean; statistic: number } | null
  significant: boolean
  summary: { en: string; fr: string }
  caveats: string[]
}

export type RegionGeometry =
  | { type: 'Polygon'; coordinates: number[][][] }
  | { type: 'MultiPolygon'; coordinates: number[][][][] }

export interface Comparison {
  a: Analysis
  b: Analysis
}

export interface MapLayer {
  slope_unit: string
  scale_min: number
  scale_max: number
  minzoom: number
  maxzoom: number
  palette: { negative: string; zero: string; positive: string }
  urls: { slope: string; nonsignificant: string }
  statistics: {
    valid_cells: number
    significant_increase_cells: number
    significant_decrease_cells: number
    non_significant_cells: number
  }
}

export interface ExternalSeriesResult {
  variable: string
  label: string
  source: string
  unit: string
  rate_unit: string
  period: { start: string; end: string }
  time: string[]
  value: Array<number | null>
  seasonal: Array<number | null>
  anomaly: Array<number | null>
  trend: TrendInfo
  significant: boolean
  summary: { en: string; fr: string }
  caveats: string[]
  metadata: { source: string; n_months: number }
}

export interface CuahsiSeries {
  id: string
  site: string
  location: string
  variable: string
  variable_code: string
  unit: string
  start: string
  end: string
  latitude: number
  longitude: number
  service: string
  organization: string
  value_count: number
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
  catalog: () => getJson<VariableInfo[]>('/api/catalog'),
  regions: () => getJson<RegionInfo[]>('/api/regions'),
  analyzeExternal: (payload: { csv_text: string; date_column: string; value_column: string; label: string; source: string; unit: string }) =>
    postJson<ExternalSeriesResult>('/api/external/analyze', payload),
  cuahsiSearch: (payload: { bounds: [number, number, number, number]; start: string; end: string; keyword: string }) =>
    postJson<CuahsiSeries[]>('/api/cuahsi/search', payload),
  cuahsiAnalyze: (payload: { bounds: [number, number, number, number]; start: string; end: string; keyword: string; series_id: string }) =>
    postJson<ExternalSeriesResult>('/api/cuahsi/analyze', payload),
  suggest: (theme: string, place: string) =>
    getJson<Array<{ variable: string; name: string; definition: string; available: boolean; message: string; region_id?: string | null }>>(
      `/api/suggest?theme=${encodeURIComponent(theme)}&place=${encodeURIComponent(place)}`,
    ),
  region: (variable: string, bounds: [number, number, number, number], label: string, start?: string, end?: string, geometry?: RegionGeometry) =>
    postJson<Analysis>('/api/region', { variable, bounds, label, start, end, ...(geometry ? { geometry } : {}) }),
  point: (variable: string, lat: number, lon: number, start?: string, end?: string) =>
    getJson<Analysis>(`/api/point?variable=${encodeURIComponent(variable)}&lat=${lat}&lon=${lon}${start ? `&start=${start}` : ''}${end ? `&end=${end}` : ''}`),
  map: (variable: string, window: string) => getJson<MapLayer>(`/api/trend/${encodeURIComponent(variable)}?window=${window}`),
  compare: (variable: string, a: string, b: string) =>
    getJson<Comparison>(`/api/compare?variable=${encodeURIComponent(variable)}&a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`),
  exportUrl: (options: {
    variable: string
    format: 'csv' | 'png' | 'tif'
    bounds?: [number, number, number, number]
    window?: string
    layer?: string
  }) => {
    const params = new URLSearchParams({ variable: options.variable, format: options.format })
    if (options.bounds) {
      const [west, south, east, north] = options.bounds
      params.set('west', String(west))
      params.set('south', String(south))
      params.set('east', String(east))
      params.set('north', String(north))
    }
    if (options.window) params.set('window', options.window)
    if (options.layer) params.set('layer', options.layer)
    return `${apiBase}/api/export?${params.toString()}`
  },
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
