import { describe, expect, it } from 'vitest'
import { fittedLine, formatPValue, formatRate } from './trendUtils'

describe('trend display helpers', () => {
  it('formats K/year slopes as signed K/decade rates', () => {
    expect(formatRate(0.023)).toBe('+0.23 K / decade')
    expect(formatRate(-0.01)).toBe('-0.10 K / decade')
    expect(formatRate(null)).toBe('—')
  })

  it('does not present tiny p values as zero', () => {
    expect(formatPValue(0)).toBe('< 0.001')
    expect(formatPValue(0.01234)).toBe('0.012')
    expect(formatPValue(null)).toBe('—')
  })

  it('fits a line through the least-squares center and preserves missing points', () => {
    const line = fittedLine([0, 1 / 12, null, 3 / 12], 1)
    expect(line[2]).toBeCloseTo(2 / 12)
    expect(line[0]).toBeCloseTo(0)
  })
})
