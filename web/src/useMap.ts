import { onBeforeUnmount, onMounted, ref, shallowRef, watch, type Ref } from 'vue'
import maplibregl, { type Map as MapLibreMap, type MapMouseEvent } from 'maplibre-gl'
import type { MapLayer } from './api'

const blankStyle = {
  version: 8 as const,
  sources: {
    'carto-light': {
      type: 'raster' as const,
      tiles: ['https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors © CARTO',
    },
  },
  layers: [{ id: 'carto-light', type: 'raster' as const, source: 'carto-light' }],
}

export function useMap(
  element: Ref<HTMLElement | null>,
  selectedLayer: Ref<MapLayer | null>,
  onPoint: (lat: number, lon: number) => void,
  onRegion: (bounds: [number, number, number, number]) => void,
) {
  const map = shallowRef<MapLibreMap | null>(null)
  const drawing = ref(false)
  let dragStart: [number, number] | null = null
  let ignoreNextClick = false

  const transparentImage = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/2ioAAAAASUVORK5CYII='
  const worldCoordinates: [[number, number], [number, number], [number, number], [number, number]] = [
    [-180, 90], [180, 90], [180, -90], [-180, -90],
  ]

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

  onMounted(() => {
    if (!element.value) return
    const instance = new maplibregl.Map({
      container: element.value,
      style: blankStyle,
      center: [5, 12],
      zoom: 1.35,
      minZoom: 0.75,
      maxZoom: 7,
    })
    instance.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    instance.on('load', () => {
      const coordinates = selectedLayer.value?.bounds ?? worldCoordinates
      instance.addSource('slope-overlay', {
        type: 'image',
        url: selectedLayer.value?.urls.slope ?? transparentImage,
        coordinates,
      })
      instance.addLayer({ id: 'slope-overlay', type: 'raster', source: 'slope-overlay', paint: { 'raster-opacity': 0.72 } })
      instance.addSource('significance-overlay', {
        type: 'image',
        url: selectedLayer.value?.urls.nonsignificant ?? transparentImage,
        coordinates,
      })
      instance.addLayer({ id: 'significance-overlay', type: 'raster', source: 'significance-overlay', paint: { 'raster-opacity': 0.8 } })
    })
    instance.on('click', (event: MapMouseEvent) => {
      if (ignoreNextClick) {
        ignoreNextClick = false
        return
      }
      if (drawing.value) return
      onPoint(event.lngLat.lat, event.lngLat.lng)
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
  })

  watch(selectedLayer, (layer) => {
    const instance = map.value
    if (!instance || !layer) return
    const update = () => {
      const slope = instance.getSource('slope-overlay') as maplibregl.ImageSource | undefined
      const significance = instance.getSource('significance-overlay') as maplibregl.ImageSource | undefined
      slope?.updateImage({ url: layer.urls.slope, coordinates: layer.bounds })
      significance?.updateImage({ url: layer.urls.nonsignificant, coordinates: layer.bounds })
    }
    if (instance.isStyleLoaded()) update()
    else instance.once('load', update)
  }, { immediate: true })

  onBeforeUnmount(() => map.value?.remove())
  return { map, drawing, startDrawing, cancelDrawing }
}
