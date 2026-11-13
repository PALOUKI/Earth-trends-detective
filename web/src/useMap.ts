import { onBeforeUnmount, ref, shallowRef, watch, type Ref } from 'vue'
import maplibregl, { type Map as MapLibreMap, type MapMouseEvent } from 'maplibre-gl'
import type { MapLayer } from './api'
import { normalizeLongitude } from './trendUtils'

const blankStyle = {
  version: 8 as const,
  sources: {
    gibs: {
      type: 'raster' as const,
      tiles: [
        'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_NextGeneration/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg',
      ],
      tileSize: 256,
      attribution: 'NASA Global Imagery Browse Services (GIBS)',
    },
  },
  layers: [{
    id: 'gibs',
    type: 'raster' as const,
    source: 'gibs',
    paint: { 'raster-saturation': -0.2, 'raster-contrast': -0.05 },
  }],
}

export function useMap(
  element: Ref<HTMLElement | null>,
  selectedLayer: Ref<MapLayer | null>,
  selectedBounds: Ref<[number, number, number, number]>,
  slopeVisible: Ref<boolean>,
  significanceVisible: Ref<boolean>,
  slopeOpacity: Ref<number>,
  onPoint: (lat: number, lon: number) => void,
  onRegion: (bounds: [number, number, number, number]) => void,
) {
  const map = shallowRef<MapLibreMap | null>(null)
  const drawing = ref(false)
  let dragStart: [number, number] | null = null
  let ignoreNextClick = false

  function moveSelectedRegionToFront(instance: MapLibreMap) {
    if (instance.getLayer('selected-region-fill')) instance.moveLayer('selected-region-fill')
    if (instance.getLayer('selected-region-line')) instance.moveLayer('selected-region-line')
  }

  function applyTrendLayers(instance: MapLibreMap, layer: MapLayer) {
    const addOrUpdateRaster = (id: string, url: string, opacity: number, visible: boolean) => {
      const existing = instance.getSource(id) as maplibregl.RasterTileSource | undefined
      if (existing) {
        existing.setTiles([url])
      } else {
        instance.addSource(id, {
          type: 'raster',
          tiles: [url],
          tileSize: 256,
          minzoom: layer.minzoom,
          maxzoom: layer.maxzoom,
          bounds: [-180, -85.051129, 180, 85.051129],
        })
      }
      if (!instance.getLayer(id)) {
        instance.addLayer({ id, type: 'raster', source: id, paint: { 'raster-opacity': opacity } })
      } else {
        instance.setPaintProperty(id, 'raster-opacity', opacity)
      }
      instance.setLayoutProperty(id, 'visibility', visible ? 'visible' : 'none')
    }
    addOrUpdateRaster('slope-overlay', layer.urls.slope, slopeOpacity.value / 100, slopeVisible.value)
    addOrUpdateRaster('significance-overlay', layer.urls.nonsignificant, 0.82, significanceVisible.value)
    moveSelectedRegionToFront(instance)
  }

  function drawBounds(mapInstance: MapLibreMap, start: [number, number], end: [number, number]) {
    const west = Math.min(start[0], end[0])
    const east = Math.max(start[0], end[0])
    const south = Math.min(start[1], end[1])
    const north = Math.max(start[1], end[1])
    const geometry = {
      type: 'Feature' as const,
      properties: {},
      geometry: {
        type: 'Polygon' as const,
        coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]],
      },
    }
    const source = mapInstance.getSource('selected-region') as maplibregl.GeoJSONSource | undefined
    if (source) source.setData(geometry)
    else mapInstance.addSource('selected-region', { type: 'geojson', data: geometry })
    if (!mapInstance.getLayer('selected-region-fill')) {
      mapInstance.addLayer({ id: 'selected-region-fill', type: 'fill', source: 'selected-region', paint: { 'fill-color': '#0b3d91', 'fill-opacity': 0.12 } })
      mapInstance.addLayer({ id: 'selected-region-line', type: 'line', source: 'selected-region', paint: { 'line-color': '#0b3d91', 'line-width': 2, 'line-dasharray': [2, 1] } })
    }
    moveSelectedRegionToFront(mapInstance)
  }

  function showSelectedRegion(instance: MapLibreMap, bounds: [number, number, number, number]) {
    if (!instance.isStyleLoaded()) {
      instance.once('load', () => showSelectedRegion(instance, bounds))
      return
    }
    const [west, south, east, rawNorth] = bounds
    const north = Math.min(85, rawNorth)
    drawBounds(instance, [west, south], [east, north])
    instance.fitBounds([[west, south], [east, north]], {
      padding: { top: 70, right: 45, bottom: 45, left: 45 },
      maxZoom: 5,
      duration: 700,
    })
  }

  function clearSelectedRegion() {
    const source = map.value?.getSource('selected-region') as maplibregl.GeoJSONSource | undefined
    source?.setData({ type: 'FeatureCollection', features: [] })
  }

  function startDrawing() {
    drawing.value = true
    if (map.value) map.value.getCanvas().style.cursor = 'crosshair'
  }

  function cancelDrawing() {
    drawing.value = false
    dragStart = null
    if (map.value) map.value.getCanvas().style.cursor = ''
  }

  function resizeMap() {
    const instance = map.value
    if (!instance) return
    instance.resize()
    showSelectedRegion(instance, selectedBounds.value)
  }

  watch(element, (container) => {
    if (!container) {
      map.value?.remove()
      map.value = null
      return
    }
    if (map.value?.getContainer() === container) return
    map.value?.remove()
    const instance = new maplibregl.Map({
      container,
      style: blankStyle,
      center: [5, 12],
      zoom: 1.35,
      minZoom: 0.75,
      maxZoom: 7,
      renderWorldCopies: false,
    })
    instance.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    instance.on('load', () => {
      if (selectedLayer.value) applyTrendLayers(instance, selectedLayer.value)
      // The map is recreated when navigating from the landing page. Reapply the
      // current selection after its style and raster layers have finished loading.
      showSelectedRegion(instance, selectedBounds.value)
    })
    instance.on('click', (event: MapMouseEvent) => {
      if (ignoreNextClick) {
        ignoreNextClick = false
        return
      }
      if (drawing.value) return
      onPoint(event.lngLat.lat, normalizeLongitude(event.lngLat.lng))
    })
    instance.on('mousedown', (event) => {
      if (!drawing.value) return
      event.preventDefault()
      dragStart = [event.lngLat.lng, event.lngLat.lat]
      instance.dragPan.disable()
    })
    instance.on('mousemove', (event) => {
      if (drawing.value && dragStart) drawBounds(instance, dragStart, [event.lngLat.lng, event.lngLat.lat])
    })
    instance.on('mouseup', (event) => {
      if (!drawing.value || !dragStart) return
      const bounds: [number, number, number, number] = [
        Math.min(dragStart[0], event.lngLat.lng),
        Math.min(dragStart[1], event.lngLat.lat),
        Math.max(dragStart[0], event.lngLat.lng),
        Math.max(dragStart[1], event.lngLat.lat),
      ]
      ignoreNextClick = true
      instance.dragPan.enable()
      cancelDrawing()
      if (bounds[0] !== bounds[2] && bounds[1] !== bounds[3]) onRegion(bounds)
    })
    map.value = instance
  }, { immediate: true, flush: 'post' })

  watch([selectedBounds, map], ([bounds, instance]) => {
    if (instance) showSelectedRegion(instance, bounds)
  }, { immediate: true, flush: 'post' })

  watch([selectedLayer, slopeVisible, significanceVisible, slopeOpacity], ([layer]) => {
    const instance = map.value
    if (!instance) return
    if (!layer) {
      for (const id of ['significance-overlay', 'slope-overlay']) {
        if (instance.getLayer(id)) instance.removeLayer(id)
        if (instance.getSource(id)) instance.removeSource(id)
      }
      return
    }
    if (instance.isStyleLoaded()) applyTrendLayers(instance, layer)
    else instance.once('load', () => applyTrendLayers(instance, layer))
  }, { immediate: true })

  onBeforeUnmount(() => map.value?.remove())
  return { map, drawing, startDrawing, cancelDrawing, clearSelectedRegion, resizeMap }
}
