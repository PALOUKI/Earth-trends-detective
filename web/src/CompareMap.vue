<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import maplibregl, { type GeoJSONSource, type Map as MapLibreMap } from 'maplibre-gl'
import type { RegionInfo } from './api'
import { COUNTRY_GEOJSON_URL } from './countries'

const props = defineProps<{
  regions: RegionInfo[]
  regionA: string
  regionB: string
  locale: 'en' | 'fr'
  dark: boolean
  labelA: string
  labelB: string
}>()

const container = ref<HTMLElement | null>(null)
let map: MapLibreMap | null = null
let resizeObserver: ResizeObserver | null = null

const colors = ['#e7f434', '#ff654f']

function selectedRegions() {
  return [props.regions.find((item) => item.id === props.regionA), props.regions.find((item) => item.id === props.regionB)]
}

function featureCollection() {
  const features = selectedRegions().flatMap((region, index) => {
    if (!region) return []
    const [west, south, east, north] = region.bounds
    const label = props.locale === 'fr' ? region.name_fr : region.name
    return [{
      type: 'Feature' as const,
      properties: { id: `region-${index}`, label, color: colors[index], number: index === 0 ? 'A' : 'B' },
      geometry: { type: 'Polygon' as const, coordinates: [[[west, south], [east, south], [east, north], [west, north], [west, south]]] },
    }]
  })
  return { type: 'FeatureCollection' as const, features }
}

function updateMap(fit = true) {
  if (!map) return
  const source = map.getSource('compareRegions') as GeoJSONSource | undefined
  if (!source) return
  source.setData(featureCollection())
  if (!fit) return
  const regions = selectedRegions().filter((item): item is RegionInfo => Boolean(item))
  if (!regions.length) return
  const west = Math.min(...regions.map((item) => item.bounds[0]))
  const south = Math.min(...regions.map((item) => item.bounds[1]))
  const east = Math.max(...regions.map((item) => item.bounds[2]))
  const north = Math.max(...regions.map((item) => item.bounds[3]))
  map.fitBounds([[west, south], [east, north]], { padding: 82, maxZoom: 2.8, duration: 650 })
}

onMounted(() => {
  if (!container.value) return
  map = new maplibregl.Map({
    container: container.value,
    style: {
      version: 8,
      sources: {
        blueMarble: {
          type: 'raster',
          tiles: ['https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_NextGeneration/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg'],
          tileSize: 256,
          attribution: 'NASA Global Imagery Browse Services (GIBS)',
        },
      },
      layers: [
        { id: 'blueMarble', type: 'raster', source: 'blueMarble', paint: { 'raster-saturation': -0.15 } },
      ],
    },
    center: [0, 10],
    zoom: 1,
    minZoom: 0.7,
    maxZoom: 7,
    renderWorldCopies: false,
  })
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
  map.on('load', () => {
    map?.addSource('country-boundaries', { type: 'geojson', data: COUNTRY_GEOJSON_URL })
    map?.addLayer({ id: 'compare-country-borders', type: 'line', source: 'country-boundaries', paint: { 'line-color': '#fff', 'line-opacity': 0.9, 'line-width': ['interpolate', ['linear'], ['zoom'], 0, 0.45, 3, 1, 5, 1.5] } })
    map?.addLayer({ id: 'compare-country-labels', type: 'symbol', source: 'country-boundaries', layout: { 'text-field': ['get', props.locale === 'fr' ? 'NAME_FR' : 'NAME'], 'text-font': ['Open Sans Regular', 'Arial Unicode MS Regular'], 'text-size': ['interpolate', ['linear'], ['zoom'], 1, 9, 3, 11, 5, 14], 'text-max-width': 8, 'text-padding': 3 }, paint: { 'text-color': '#fff', 'text-halo-color': '#152437', 'text-halo-width': 1.4, 'text-opacity': ['interpolate', ['linear'], ['zoom'], 1, 0.72, 3, 1] } })
    map?.addSource('compare-regions', { type: 'geojson', data: featureCollection() })
    map?.addLayer({ id: 'compare-regions-fill', type: 'fill', source: 'compare-regions', paint: { 'fill-color': ['get', 'color'], 'fill-opacity': 0.42 } })
    map?.addLayer({ id: 'compare-regions-outline', type: 'line', source: 'compare-regions', paint: { 'line-color': ['get', 'color'], 'line-width': 4, 'line-opacity': 1, 'line-dasharray': [2, 1] } })
    map?.addLayer({ id: 'compare-regions-label', type: 'symbol', source: 'compare-regions', layout: { 'text-field': ['concat', ['get', 'number'], ' · ', ['get', 'label']], 'text-size': 13, 'text-font': ['Open Sans Semibold', 'Arial Unicode MS Regular'], 'text-allow-overlap': true }, paint: { 'text-color': '#fff', 'text-halo-color': '#101828', 'text-halo-width': 2 } })
    updateMap()
  })
  resizeObserver = new ResizeObserver(() => map?.resize())
  resizeObserver.observe(container.value)
})

watch(() => [props.regionA, props.regionB, props.locale, props.regions], () => updateMap(), { deep: true })
watch(() => props.dark, (dark) => {
  if (!map) return
  if (map.getLayer('compare-regions-label')) map.setPaintProperty('compare-regions-label', 'text-halo-color', dark ? '#151622' : '#101828')
})
watch(() => props.locale, (locale) => {
  if (map?.getLayer('compare-country-labels')) map.setLayoutProperty('compare-country-labels', 'text-field', ['get', locale === 'fr' ? 'NAME_FR' : 'NAME'])
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  map?.remove()
})
</script>

<template>
  <section class="compare-map-card" :class="{ 'compare-map-dark': dark }" :aria-label="locale === 'fr' ? 'Carte des deux régions comparées' : 'Map of the two regions being compared'">
    <header class="compare-map-heading">
      <span class="eyebrow">{{ locale === 'fr' ? 'APERÇU GÉOGRAPHIQUE' : 'GEOGRAPHIC PREVIEW' }}</span>
      <div class="compare-map-key">
        <span><i class="compare-map-swatch region-a"></i>A · {{ labelA }}</span>
        <span><i class="compare-map-swatch region-b"></i>B · {{ labelB }}</span>
      </div>
    </header>
    <div ref="container" class="compare-map-canvas"></div>
    <p class="compare-map-note">{{ locale === 'fr' ? 'Les contours montrent les emprises rectangulaires d’analyse sélectionnées.' : 'Outlines show the selected rectangular analysis extents.' }}</p>
  </section>
</template>
