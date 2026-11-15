import type { RegionGeometry } from './api'

export const COUNTRY_GEOJSON_URL = 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson'
export const ECOREGION_SERVICE_URL = 'https://services.arcgis.com/P3ePLMYs2RVChkJx/arcgis/rest/services/Resolve_Ecoregions/FeatureServer/0'
export const ECOREGION_QUERY_URL = `${ECOREGION_SERVICE_URL}/query`

export interface CountryOption {
  name: string
  name_fr: string
  anchor: { lon: number; lat: number }
}

export interface EcoregionFeature {
  type: 'Feature'
  geometry: RegionGeometry
  properties: {
    ECO_ID: number
    ECO_NAME: string
    BIOME_NAME: string
    REALM: string
  }
}

export interface EcoregionSelection {
  feature: EcoregionFeature
  bounds: [number, number, number, number]
}

interface CountryFeatureCollection {
  features?: Array<{
    properties?: { NAME?: unknown; NAME_FR?: unknown; LABEL_X?: unknown; LABEL_Y?: unknown }
  }>
}

interface EcoregionFeatureCollection {
  features?: EcoregionFeature[]
}

let countriesRequest: Promise<CountryOption[]> | null = null

function cleanName(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

export async function loadCountries(): Promise<CountryOption[]> {
  if (!countriesRequest) {
    countriesRequest = (async () => {
      const response = await fetch(COUNTRY_GEOJSON_URL)
      if (!response.ok) throw new Error(`Country list request failed (${response.status})`)
      const data = await response.json() as CountryFeatureCollection
      return (data.features ?? []).flatMap((feature) => {
        const name = cleanName(feature.properties?.NAME)
        const name_fr = cleanName(feature.properties?.NAME_FR) || name
        const lon = Number(feature.properties?.LABEL_X)
        const lat = Number(feature.properties?.LABEL_Y)
        if (!name || !Number.isFinite(lon) || !Number.isFinite(lat)) return []
        return [{ name, name_fr, anchor: { lon, lat } }]
      }).sort((a, b) => a.name.localeCompare(b.name))
    })()
  }

  try {
    return await countriesRequest
  } catch (error) {
    countriesRequest = null
    throw error
  }
}

export async function loadEcoregionAtPoint(point: CountryOption['anchor']): Promise<EcoregionSelection> {
  const params = new URLSearchParams({
    where: '1=1',
    geometry: `${point.lon},${point.lat}`,
    geometryType: 'esriGeometryPoint',
    inSR: '4326',
    spatialRel: 'esriSpatialRelIntersects',
    outFields: 'ECO_ID,ECO_NAME,BIOME_NAME,REALM',
    returnGeometry: 'true',
    outSR: '4326',
    f: 'geojson',
  })
  const response = await fetch(`${ECOREGION_QUERY_URL}?${params}`)
  if (!response.ok) throw new Error(`Ecoregion request failed (${response.status})`)
  const data = await response.json() as EcoregionFeatureCollection
  const feature = selectEcoregionFeature(data.features ?? [])
  if (!feature) throw new Error('No terrestrial ecoregion found at the selected country reference point')
  return { feature, bounds: geometryBounds(feature.geometry) }
}

export function selectEcoregionFeature(features: EcoregionFeature[]): EcoregionFeature | undefined {
  return features.find((item) => item.geometry && item.properties?.ECO_NAME && item.properties?.BIOME_NAME)
}

export function geometryBounds(geometry: RegionGeometry): [number, number, number, number] {
  const coordinates: number[][] = []
  const visit = (value: unknown) => {
    if (!Array.isArray(value)) return
    if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') {
      coordinates.push([value[0], value[1]])
      return
    }
    for (const child of value) visit(child)
  }
  visit(geometry.coordinates)
  if (!coordinates.length) throw new Error('The selected ecoregion has no coordinates')
  return [
    Math.min(...coordinates.map(([lon]) => lon)),
    Math.min(...coordinates.map(([, lat]) => lat)),
    Math.max(...coordinates.map(([lon]) => lon)),
    Math.max(...coordinates.map(([, lat]) => lat)),
  ]
}

function normalizeName(value: string): string {
  return value.normalize('NFD').replace(/\p{Diacritic}/gu, '').trim().toLocaleLowerCase()
}

export function findCountry(countries: CountryOption[], query: string): CountryOption | undefined {
  const normalizedQuery = normalizeName(query)
  if (!normalizedQuery) return undefined
  return countries.find((country) =>
    normalizeName(country.name) === normalizedQuery || normalizeName(country.name_fr) === normalizedQuery)
}
