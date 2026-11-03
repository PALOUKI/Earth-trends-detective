export const variableIdsByTheme = {
  climate: ['gistemp_tas_anom', 'airs_surface_air_temp'],
  water: ['gpm_precipitation', 'merra2_flux', 'gldas_noah_monthly'],
  vegetation: ['modis_ndvi', 'modis_evi'],
  air: ['omi_no2'],
} as const

export type WizardTheme = keyof typeof variableIdsByTheme

export function variablesForTheme(theme: WizardTheme): readonly string[] {
  return variableIdsByTheme[theme]
}
