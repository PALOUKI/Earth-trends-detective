<script setup lang="ts">
import { computed, ref } from 'vue'
import type { CuahsiSeries, ExternalSeriesResult, RegionInfo } from './api'
import { api } from './api'
import { formatPValue, formatRate } from './trendUtils'

const props = defineProps<{ locale: 'en' | 'fr'; regions: RegionInfo[] }>()
const fr = computed(() => props.locale === 'fr')
const source = ref('giovanni')
const csvText = ref('')
const fileName = ref('')
const dateColumn = ref('')
const valueColumn = ref('')
const label = ref('')
const unit = ref('')
const result = ref<ExternalSeriesResult | null>(null)
const error = ref('')
const loading = ref(false)
const cuahsiKeyword = ref('Discharge, stream')
const cuahsiRegionId = ref('')
const cuahsiStart = ref('2000-01-01')
const cuahsiEnd = ref(new Date().toISOString().slice(0, 10))
const cuahsiResults = ref<CuahsiSeries[]>([])
const cuahsiHasSearched = ref(false)
const cuahsiSearching = ref(false)
const cuahsiLoadingId = ref('')
const selectedCuahsiRegion = computed(() => props.regions.find((item) => item.id === cuahsiRegionId.value) ?? props.regions[0])

const strings = computed(() => fr.value ? {
  title: 'Autres sources de séries', intro: 'Utilisez les outils recommandés par le défi et CUAHSI, puis analysez ici les séries téléchargées avec les mêmes tests statistiques.',
  sources: 'Ouvrir une source', how: '1. Choisissez une source et téléchargez une série mensuelle au format CSV.',
  how2: '2. Importez le fichier, choisissez les colonnes date et valeur, puis lancez l’analyse.',
  giovanni: 'Giovanni · séries de variables NASA par région', hydrology: 'NASA Hydrology Time Series', appeears: 'AppEEARS · extraction spatiale et séries ponctuelles', noaa: 'NOAA Climate Data Online · stations météo', cuahsi: 'CUAHSI HydroClient · hydrologie de stations',
  noteGiovanni: 'Dans Giovanni, choisissez Area-Averaged Time Series, la variable, la période et la zone ; téléchargez les valeurs CSV.',
  noteHydrology: 'Ouvre le catalogue Hydrology Time Series du NASA GES DISC. Selon le produit, utilisez son interface pour générer/télécharger une série.',
  noteAppeears: 'Créez une tâche Point Sample pour un point, puis téléchargez le CSV de la série et ses métadonnées.',
  noteNoaa: 'CDO donne accès aux observations de stations ; son API nécessite un jeton NOAA. Vous pouvez télécharger les données depuis l’interface web puis importer le CSV ici.',
  noteCuahsi: 'Choisissez une région et une mesure ci-dessous : la recherche, le téléchargement et l’analyse se font directement ici.',
  file: 'Fichier CSV', date: 'Colonne date', value: 'Colonne valeur', seriesLabel: 'Nom de la variable et lieu', unitLabel: 'Unité', analyze: 'Analyser la série', wait: 'Analyse…',
  result: 'Résultat de tendance', slope: 'Pente OLS', p: 'p OLS', months: 'mois mensuels', raw: 'Valeur mensuelle', anomaly: 'Anomalie désaisonnalisée',
  warning: 'Les séries importées sont ramenées à une moyenne mensuelle. La source, l’unité et les métadonnées du CSV ne sont pas vérifiées automatiquement.', significant: 'Significatif selon p OLS < 0,05', noSignificant: 'Pas (encore) significatif selon p OLS ≥ 0,05',
  badCsv: 'Choisissez un CSV avec une colonne de dates et une colonne numérique.',
  manualTitle: 'Importer manuellement un CSV (autres portails)',
  cuahsiTitle: 'Hydrologie · recherche directe CUAHSI', cuahsiArea: 'Région', cuahsiKeyword: 'Mesure recherchée', cuahsiStart: 'Depuis', cuahsiEnd: 'Jusqu’au', cuahsiSearch: 'Chercher les séries disponibles', cuahsiSearching: 'Recherche des stations…', cuahsiChoose: 'Analyser cette station', cuahsiLoading: 'Téléchargement et analyse…', cuahsiNone: 'Aucune série trouvée pour cette zone et ces filtres. Essayez une zone plus grande ou une autre mesure.', cuahsiResults: 'Séries trouvées', cuahsiCaveat: 'Chaque résultat correspond à une station de mesure située dans ou près de la région choisie.',
} : {
  title: 'More time-series sources', intro: 'Use the resources recommended by the challenge and CUAHSI, then analyze downloaded series here with the same statistical tests.',
  sources: 'Open a source', how: '1. Choose a source and download a monthly time series as CSV.',
  how2: '2. Import the file, select date and value columns, then run the analysis.',
  giovanni: 'Giovanni · regional NASA variable series', hydrology: 'NASA Hydrology Time Series', appeears: 'AppEEARS · spatial extraction and point time series', noaa: 'NOAA Climate Data Online · weather stations', cuahsi: 'CUAHSI HydroClient · hydrology stations',
  noteGiovanni: 'In Giovanni, choose Area-Averaged Time Series, a variable, period, and area; download the CSV values.',
  noteHydrology: 'Opens the NASA GES DISC Hydrology Time Series catalog. Use the product interface to generate/download a series where available.',
  noteAppeears: 'Create a Point Sample task for a location, then download the time-series CSV and its metadata.',
  noteNoaa: 'CDO provides station observations; its API requires a NOAA token. You can download data from its website and import the CSV here.',
  noteCuahsi: 'Choose a region and measurement below; search, retrieval, and analysis run directly here.',
  file: 'CSV file', date: 'Date column', value: 'Value column', seriesLabel: 'Variable and place', unitLabel: 'Unit', analyze: 'Analyze series', wait: 'Analyzing…',
  result: 'Trend result', slope: 'OLS slope', p: 'OLS p-value', months: 'monthly records', raw: 'Monthly value', anomaly: 'Deseasonalized anomaly',
  warning: 'Imported series are aggregated to monthly means. CSV source, units, and metadata are not automatically verified.', significant: 'Significant by OLS p < 0.05', noSignificant: 'Not (yet) significant by OLS p ≥ 0.05',
  badCsv: 'Choose a CSV with a date column and a numeric value column.',
  manualTitle: 'Manually import a CSV (other portals)',
  cuahsiTitle: 'Hydrology · search CUAHSI directly', cuahsiArea: 'Region', cuahsiKeyword: 'Measurement', cuahsiStart: 'From', cuahsiEnd: 'To', cuahsiSearch: 'Find available series', cuahsiSearching: 'Searching stations…', cuahsiChoose: 'Analyze this station', cuahsiLoading: 'Downloading and analyzing…', cuahsiNone: 'No series found for this area and filter. Try a larger area or another measurement.', cuahsiResults: 'Series found', cuahsiCaveat: 'Each result is a measurement station located in or near the selected region.',
})

const headers = computed(() => {
  const firstLine = csvText.value.split(/\r?\n/, 1)[0] ?? ''
  return firstLine.split(',').map((part) => part.trim().replace(/^"|"$/g, ''))
})
const chartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: [strings.value.raw, strings.value.anomaly] },
  grid: { left: 54, right: 20, top: 45, bottom: 40 },
  xAxis: { type: 'category', data: result.value?.time ?? [], boundaryGap: false },
  yAxis: { type: 'value', name: result.value?.unit },
  series: [
    { name: strings.value.raw, type: 'line', showSymbol: false, connectNulls: false, data: result.value?.value ?? [] },
    { name: strings.value.anomaly, type: 'line', showSymbol: false, connectNulls: false, data: result.value?.anomaly ?? [] },
  ],
}))

async function loadFile(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  error.value = ''
  result.value = null
  if (file.size > 5_000_000) { error.value = 'CSV must be 5 MB or smaller.'; return }
  fileName.value = file.name
  csvText.value = await file.text()
  dateColumn.value = headers.value.find((header) => /date|time|month/i.test(header)) ?? headers.value[0] ?? ''
  valueColumn.value = headers.value.find((header) => header !== dateColumn.value && /value|mean|data|ndvi|evi|temp|precip|flow|discharge|tavg/i.test(header))
    ?? headers.value.find((header) => header !== dateColumn.value) ?? ''
}

async function analyze() {
  if (!csvText.value || !dateColumn.value || !valueColumn.value || !label.value.trim() || !unit.value.trim()) {
    error.value = strings.value.badCsv
    return
  }
  loading.value = true
  error.value = ''
  try {
    result.value = await api.analyzeExternal({
      csv_text: csvText.value, date_column: dateColumn.value, value_column: valueColumn.value,
      label: label.value.trim(), unit: unit.value.trim(), source: source.value,
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : strings.value.badCsv
  } finally {
    loading.value = false
  }
}

async function searchCuahsi() {
  if (!selectedCuahsiRegion.value) return
  cuahsiSearching.value = true
  cuahsiHasSearched.value = true
  error.value = ''
  result.value = null
  try {
    cuahsiResults.value = await api.cuahsiSearch({
      bounds: selectedCuahsiRegion.value.bounds,
      start: cuahsiStart.value,
      end: cuahsiEnd.value,
      keyword: cuahsiKeyword.value.trim(),
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : strings.value.cuahsiNone
  } finally {
    cuahsiSearching.value = false
  }
}

async function analyzeCuahsi(series: CuahsiSeries) {
  if (!selectedCuahsiRegion.value) return
  cuahsiLoadingId.value = series.id
  error.value = ''
  try {
    result.value = await api.cuahsiAnalyze({
      bounds: selectedCuahsiRegion.value.bounds,
      start: cuahsiStart.value,
      end: cuahsiEnd.value,
      keyword: cuahsiKeyword.value.trim(),
      series_id: series.id,
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : strings.value.cuahsiNone
  } finally {
    cuahsiLoadingId.value = ''
  }
}
</script>

<template>
  <main class="content-page external-page">
    <div class="content-heading"><span class="eyebrow">NASA · NOAA · EXTERNAL SERIES</span><h1 class="resources-page-title">{{ strings.title }}</h1><p>{{ strings.intro }}</p></div>
    <section class="resource-grid" :aria-label="strings.sources">
      <article><h2>{{ strings.giovanni }}</h2><p>{{ strings.noteGiovanni }}</p><a href="https://giovanni.gsfc.nasa.gov/giovanni/" target="_blank" rel="noreferrer">Open Giovanni ↗</a></article>
      <article><h2>{{ strings.hydrology }}</h2><p>{{ strings.noteHydrology }}</p><a href="https://disc.gsfc.nasa.gov/information/tools?title=Hydrology%20Time%20Series" target="_blank" rel="noreferrer">Open NASA GES DISC ↗</a></article>
      <article><h2>{{ strings.appeears }}</h2><p>{{ strings.noteAppeears }}</p><a href="https://appeears.earthdatacloud.nasa.gov/" target="_blank" rel="noreferrer">Open AppEEARS ↗</a></article>
      <article><h2>{{ strings.noaa }}</h2><p>{{ strings.noteNoaa }}</p><a href="https://www.ncei.noaa.gov/cdo-web/" target="_blank" rel="noreferrer">Open NOAA CDO ↗</a></article>
    </section>
    <section class="cuahsi-search-panel">
      <div class="cuahsi-heading"><div><span class="eyebrow">CUAHSI HYDROCLIENT</span><h2>{{ strings.cuahsiTitle }}</h2></div><span class="status-badge status-ready">{{ fr ? 'Recherche intégrée' : 'Built-in search' }}</span></div>
      <p>{{ strings.cuahsiCaveat }}</p>
      <div class="cuahsi-search-controls">
        <label class="field-label">{{ strings.cuahsiArea }}<select v-model="cuahsiRegionId"><option v-for="region in regions" :key="region.id" :value="region.id">{{ fr ? region.name_fr : region.name }}</option></select></label>
        <label class="field-label">{{ strings.cuahsiKeyword }}<select v-model="cuahsiKeyword"><option value="Discharge, stream">{{ fr ? 'Débit de rivière' : 'Stream discharge' }}</option><option value="Precipitation">{{ fr ? 'Précipitations' : 'Precipitation' }}</option><option value="Soil moisture">{{ fr ? 'Humidité du sol' : 'Soil moisture' }}</option><option value="Water level">{{ fr ? 'Niveau d’eau' : 'Water level' }}</option></select></label>
        <label class="field-label">{{ strings.cuahsiStart }}<input v-model="cuahsiStart" class="text-input" type="date" /></label>
        <label class="field-label">{{ strings.cuahsiEnd }}<input v-model="cuahsiEnd" class="text-input" type="date" /></label>
      </div>
      <button class="button primary" :disabled="cuahsiSearching || !selectedCuahsiRegion" @click="searchCuahsi">{{ cuahsiSearching ? strings.cuahsiSearching : strings.cuahsiSearch }}</button>
      <p v-if="cuahsiResults.length" class="eyebrow cuahsi-results-count">{{ cuahsiResults.length }} {{ strings.cuahsiResults }}</p>
      <div v-if="cuahsiResults.length" class="cuahsi-result-list">
        <article v-for="series in cuahsiResults" :key="series.id" class="cuahsi-result-item">
          <div><strong>{{ series.variable }}</strong><span>{{ series.site }} · {{ series.organization || series.service }}</span><small>{{ series.start }} — {{ series.end }} · {{ series.unit }} · {{ series.latitude.toFixed(3) }}, {{ series.longitude.toFixed(3) }}</small></div>
          <button class="button secondary compact" :disabled="!!cuahsiLoadingId" @click="analyzeCuahsi(series)">{{ cuahsiLoadingId === series.id ? strings.cuahsiLoading : strings.cuahsiChoose }}</button>
        </article>
      </div>
      <p v-else-if="cuahsiHasSearched && !cuahsiSearching && error === ''" class="field-help">{{ strings.cuahsiNone }}</p>
      <div v-if="error" class="error-message" role="alert">{{ error }}</div>
    </section>
    <details class="external-import">
      <summary>{{ strings.manualTitle }}</summary>
      <span class="eyebrow">{{ strings.how }}</span><p>{{ strings.how2 }}</p>
      <label class="field-label">{{ strings.sources }}<select v-model="source"><option value="giovanni">{{ strings.giovanni }}</option><option value="hydrology">{{ strings.hydrology }}</option><option value="appeears">{{ strings.appeears }}</option><option value="noaa_cdo">{{ strings.noaa }}</option></select></label>
      <label class="field-label">{{ strings.file }}<input class="text-input" type="file" accept=".csv,text/csv" @change="loadFile" /></label>
      <p v-if="fileName" class="field-help">{{ fileName }}</p>
      <div v-if="headers.length > 1" class="external-fields">
        <label class="field-label">{{ strings.date }}<select v-model="dateColumn"><option v-for="item in headers" :key="item" :value="item">{{ item }}</option></select></label>
        <label class="field-label">{{ strings.value }}<select v-model="valueColumn"><option v-for="item in headers.filter((header) => header !== dateColumn)" :key="item" :value="item">{{ item }}</option></select></label>
        <label class="field-label">{{ strings.seriesLabel }}<input v-model="label" class="text-input" required /></label>
        <label class="field-label">{{ strings.unitLabel }}<input v-model="unit" class="text-input" required /></label>
      </div>
      <p class="external-warning">{{ strings.warning }}</p>
      <div v-if="error" class="error-message" role="alert">{{ error }}</div>
      <button class="button primary" :disabled="loading || !csvText" @click="analyze">{{ loading ? strings.wait : strings.analyze }}</button>
    </details>
    <section v-if="result" class="external-result">
      <div class="result-heading"><div><span class="eyebrow">{{ strings.result }} · {{ result.period.start }} — {{ result.period.end }}</span><h2>{{ result.label }}</h2></div><span class="verdict" :class="result.significant ? 'good' : 'caution'">{{ result.significant ? strings.significant : strings.noSignificant }}</span></div>
      <div class="external-result-stats"><div><small>{{ strings.slope }}</small><strong>{{ formatRate(result.trend.slope_ols, result.rate_unit) }}</strong></div><div><small>{{ strings.p }}</small><strong>{{ formatPValue(result.trend.p_ols) }}</strong></div><div><small>{{ result.metadata.n_months }} {{ strings.months }}</small><strong>{{ result.source }}</strong></div></div>
      <VChart class="external-chart" :option="chartOption" autoresize />
      <ul><li v-for="item in result.caveats" :key="item">{{ item }}</li></ul>
    </section>
  </main>
</template>
