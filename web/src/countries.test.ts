import { describe, expect, it } from 'vitest'
import { findCountry, geometryBounds, selectEcoregionFeature, type CountryOption, type EcoregionFeature } from './countries'

const countries: CountryOption[] = [
  { name: 'Cote d’Ivoire', name_fr: 'Côte d’Ivoire', anchor: { lon: -5.5, lat: 7.5 } },
  { name: 'Togo', name_fr: 'Togo', anchor: { lon: 1.058113, lat: 8.80722 } },
]

const ecoregions: EcoregionFeature[] = [
  {
    type: 'Feature',
    geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] },
    properties: { ECO_ID: 1, ECO_NAME: 'Small region', BIOME_NAME: 'Savanna', REALM: 'Afrotropic' },
  },
  {
    type: 'Feature',
    geometry: { type: 'MultiPolygon', coordinates: [[[[2, -1], [4, -1], [4, 3], [2, 3], [2, -1]]]] },
    properties: { ECO_ID: 62, ECO_NAME: 'West Sudanian savanna', BIOME_NAME: 'Tropical & Subtropical Grasslands, Savannas & Shrublands', REALM: 'Afrotropic' },
  },
]

describe('country to ecological region lookup', () => {
  it('matches country names in either language and ignores accents', () => {
    expect(findCountry(countries, 'Côte d’Ivoire')?.name).toBe('Cote d’Ivoire')
    expect(findCountry(countries, 'Cote d’Ivoire')?.name_fr).toBe('Côte d’Ivoire')
    expect(findCountry(countries, 'Gha')).toBeUndefined()
  })

  it('uses an ecological feature returned by the point-in-region lookup', () => {
    expect(selectEcoregionFeature(ecoregions)?.properties.ECO_NAME).toBe('Small region')
    expect(selectEcoregionFeature([])).toBeUndefined()
  })

  it('calculates zoom bounds from every polygon in the selected ecoregion', () => {
    expect(geometryBounds(ecoregions[1].geometry)).toEqual([2, -1, 4, 3])
  })
})
