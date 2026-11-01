export function formatRate(value: number | null | undefined, unit = 'K'): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  const scaled = value * 10
  return `${scaled >= 0 ? '+' : ''}${scaled.toFixed(2)} ${unit} / decade`
}

export function formatPValue(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'
  return value < 0.001 ? '< 0.001' : value.toFixed(3)
}

export function normalizeLongitude(longitude: number): number {
  return ((longitude + 180) % 360 + 360) % 360 - 180
}

export function fittedLine(values: Array<number | null>, slopePerYear: number | null) {
  if (slopePerYear === null || !Number.isFinite(slopePerYear)) return values.map(() => null)
  const valid = values.flatMap((value, index) =>
    value === null || !Number.isFinite(value) ? [] : [{ value, index }],
  )
  if (!valid.length) return values.map(() => null)
  const meanValue = valid.reduce((sum, item) => sum + item.value, 0) / valid.length
  const meanTime = valid.reduce((sum, item) => sum + item.index / 12, 0) / valid.length
  const intercept = meanValue - slopePerYear * meanTime
  return values.map((_, index) => intercept + slopePerYear * index / 12)
}
