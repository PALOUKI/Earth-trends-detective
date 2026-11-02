import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from './api'

afterEach(() => vi.unstubAllGlobals())

describe('API routes used by the investigation screens', () => {
  it('builds CSV export URLs with the selected region bounds', () => {
    const url = new URL(api.exportUrl({
      variable: 'gpm_precipitation',
      format: 'csv',
      bounds: [-75, -15, -45, 5],
    }), window.location.origin)

    expect(url.pathname).toBe('/api/export')
    expect(url.searchParams.get('variable')).toBe('gpm_precipitation')
    expect(url.searchParams.get('format')).toBe('csv')
    expect(url.searchParams.get('west')).toBe('-75')
    expect(url.searchParams.get('north')).toBe('5')
  })

  it('requests comparisons from the real regional comparison endpoint', async () => {
    const response = { a: { label: 'A' }, b: { label: 'B' } }
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => response })
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.compare('gistemp_tas_anom', 'amazon', 'sahara')).resolves.toEqual(response)
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/compare?variable=gistemp_tas_anom&a=amazon&b=sahara',
    )
  })
})
