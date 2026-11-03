import { describe, expect, it } from 'vitest'
import { variableIdsByTheme, variablesForTheme } from './wizardThemes'

describe('guided investigation theme groups', () => {
  it('assigns all eight analysis variables once across the four themes', () => {
    const assigned = Object.values(variableIdsByTheme).flat()
    expect(assigned).toHaveLength(8)
    expect(new Set(assigned).size).toBe(8)
    expect(variablesForTheme('climate')).toEqual(['gistemp_tas_anom', 'airs_surface_air_temp'])
    expect(variablesForTheme('water')).toEqual([
      'gpm_precipitation', 'merra2_flux', 'gldas_noah_monthly',
    ])
    expect(variablesForTheme('vegetation')).toEqual(['modis_ndvi', 'modis_evi'])
    expect(variablesForTheme('air')).toEqual(['omi_no2'])
  })
})
