import { describe, expect, it } from 'vitest'
import { availableAnalysisWindows, comparisonDirection, fittedLine, formatPValue, formatRate, isPeriodRangeWithinCoverage, normalizeLongitude, stepMapZoom } from './trendUtils'

describe('trend display helpers', () => {
  it('formats K/year slopes as signed K/decade rates', () => {
    expect(formatRate(0.023)).toBe('+0.23 K/decade')
    expect(formatRate(-0.01)).toBe('-0.10 K/decade')
    expect(formatRate(0.002, 'index/year')).toBe('+0.02 index/decade')
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

  it('normalizes wrapped map longitudes into the API coordinate range', () => {
    expect(normalizeLongitude(256)).toBe(-104)
    expect(normalizeLongitude(180)).toBe(-180)
    expect(normalizeLongitude(-181)).toBe(179)
  })

  it('summarizes estimated regional trend directions without inferring causes', () => {
    expect(comparisonDirection(0.02, -0.01)).toBe('opposite')
    expect(comparisonDirection(0.02, 0.01)).toBe('same_up')
    expect(comparisonDirection(-0.02, -0.01)).toBe('same_down')
    expect(comparisonDirection(0, -0.01)).toBe('flat')
    expect(comparisonDirection(null, 0.01)).toBe('insufficient')
  })

  it('keeps landing map zoom between its global and maximum views', () => {
    expect(stepMapZoom(1, -1)).toBe(1)
    expect(stepMapZoom(1, 1)).toBe(1.25)
    expect(stepMapZoom(3, 1)).toBe(3)
    expect(stepMapZoom(3, -1)).toBe(2.75)
  })

  it('hides analysis windows outside a variable’s actual data coverage', () => {
    expect(availableAnalysisWindows(['full', '2010-fin', '2015-fin'], '2005-01', '2012-12'))
      .toEqual(['full', '2010-fin'])
    expect(availableAnalysisWindows(['full', '2010-fin', '2015-fin'], '2012-01', '2022-12'))
      .toEqual(['full', '2015-fin'])
    expect(availableAnalysisWindows(['full'], '2012-01', '2022-12'))
      .toEqual(['full'])
  })

  it('accepts only valid custom month ranges inside the variable coverage', () => {
    expect(isPeriodRangeWithinCoverage('2002-04', '2009-11', '2000-02', '2011-08')).toBe(true)
    expect(isPeriodRangeWithinCoverage('1999-12', '2009-11', '2000-02', '2011-08')).toBe(false)
    expect(isPeriodRangeWithinCoverage('2002-04', '2012-01', '2000-02', '2011-08')).toBe(false)
    expect(isPeriodRangeWithinCoverage('2010-01', '2009-11', '2000-02', '2011-08')).toBe(false)
    expect(isPeriodRangeWithinCoverage('2000-13', '2009-11', '2000-02', '2011-08')).toBe(false)
  })
})
