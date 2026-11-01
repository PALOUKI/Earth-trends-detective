<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { Analysis, MapLayer, RegionInfo, VariableInfo } from './api'
import { api } from './api'
import { fittedLine, formatPValue, formatRate } from './trendUtils'
import { useMap } from './useMap'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

type Locale = 'en' | 'fr'
type WindowId = 'full' | '2010-fin' | '2015-fin'
type AppPage = 'explore' | 'methods' | 'about'

const copy = {
  en: {
    explore: 'Explore', methods: 'Methods & validation', about: 'About', lang: 'Français',
    parameters: 'Analysis parameters', dataset: 'DATASET', variable: 'Variable',
    place: 'Study area', selectRegion: 'Choose a region', draw: 'Draw a rectangle',
    drawing: 'Drag on the map to draw', period: 'Analysis period', full: 'Full record',
    since2010: 'Since 2010', since2015: 'Since 2015', apply: 'Analyze region',
    chart: 'Regional time series', summary: 'Trend summary', loading: 'Analyzing GISTEMP…',
    loadingMap: 'Loading trend layer…', rate: 'Linear rate', confidence: '95% confidence interval',
    pValueHelp: 'A p-value measures how unusual these data would be if there were no trend; it is not the probability that the result is true.',
    confidenceHelp: 'The 95% interval gives a range of plausible linear rates under the model assumptions.',
    significanceHelp: 'This label compares the OLS p-value with 0.05. It does not identify a cause.',
    significant: 'Significant', notSignificant: 'Not (yet) significant', insufficient: 'Not enough data',
    longerPeriod: 'A longer time period could change this significance result.',
    ols: 'OLS t test', mk: 'Mann–Kendall', hr: 'Hamed–Rao',
    raw: 'Monthly anomaly', deseasoned: 'Deseasonalized', trend: 'Linear trend',
    guided: 'Guided investigation', demo: 'Try a guided example', demoTitle: 'Guided examples',
    startDemo: 'Explore example', next: 'Next step', finish: 'Show result', close: 'Close',
    theme: 'What interests you?', themeClimate: 'Climate', themeWater: 'Water',
    themePlants: 'Vegetation', themeAir: 'Air quality', where: 'Where should we look?',
    source: 'NASA GISS GISTEMP v4', unit: 'K / year', mapTitle: 'Global trend discovery map',
    mapHelp: 'Pink/red cells show positive warming trends; blue shows cooling. Dots mark cells that did not pass the map significance threshold. Click a cell to inspect its series.',
    noData: 'Processed GISTEMP is not available. Run `make preprocess` to generate it.',
    testConflict: 'The basic and autocorrelation-adjusted tests differ. Check the p-values and confidence interval before drawing a conclusion.',
    disclaimer: 'A significant trend describes statistical evidence of change; it does not identify its cause.',
    aboutTitle: 'Earth Trend Detective', aboutText: 'An educational tool for exploring NASA Earth observations by place and time.',
    data: 'Data & credits', limitations: 'Limitations', periodShort: 'period', coordinates: 'Selected grid cell',
    choose: 'Select',
    methodsIntro: 'The tool separates the regional analysis from the discovery map. Click a region or grid cell to see the full Base analysis.',
    m1: 'OLS fits a straight line through the deseasonalized monthly anomalies. The t test and 95% interval describe uncertainty under independent residuals.',
    m2: 'Mann–Kendall tests whether values tend to move in one direction. Sen’s slope gives a robust rate using pairwise slopes.',
    m3: 'Hamed–Rao adjusts the Mann–Kendall variance for serial dependence. The global map uses a fast OLS test followed by Benjamini–Hochberg FDR at 0.10.',
    validation: 'Validation against NASA’s published monthly global series: 561 months (1980–2026), 0.050 K RMSE; global slopes agree within 0.000001 K/year.',
    mapWindow: 'Map window',
    blankMap: 'Trend layer unavailable', point: 'Point', region: 'Region',
    dataFrequency: 'Monthly · 2° grid', fieldHelp: 'Choose an example area or drag over the map.',
    slopeLayer: 'OLS slope · K/year', nonsignificantLayer: 'dots = not significant', observations: 'months',
  },
  fr: {
    explore: 'Explorer', methods: 'Méthodes et validation', about: 'À propos', lang: 'English',
    parameters: 'Paramètres d’analyse', dataset: 'JEU DE DONNÉES', variable: 'Variable',
    place: 'Zone étudiée', selectRegion: 'Choisir une région', draw: 'Dessiner un rectangle',
    drawing: 'Tracer sur la carte', period: 'Période d’analyse', full: 'Toute la série',
    since2010: 'Depuis 2010', since2015: 'Depuis 2015', apply: 'Analyser la région',
    chart: 'Série temporelle régionale', summary: 'Résumé de tendance', loading: 'Analyse de GISTEMP…',
    loadingMap: 'Chargement de la carte…', rate: 'Taux linéaire', confidence: 'Intervalle de confiance à 95 %',
    pValueHelp: 'La valeur p indique à quel point ces données seraient inhabituelles en l’absence de tendance ; ce n’est pas la probabilité que le résultat soit vrai.',
    confidenceHelp: 'L’intervalle à 95 % donne une plage de taux linéaires plausibles sous les hypothèses du modèle.',
    significanceHelp: 'Cette étiquette compare la valeur p MCO au seuil de 0,05. Elle ne donne pas la cause.',
    significant: 'Significative', notSignificant: 'Pas (encore) significative', insufficient: 'Données insuffisantes',
    longerPeriod: 'Une période plus longue pourrait changer ce résultat de significativité.',
    ols: 'Test t MCO', mk: 'Mann–Kendall', hr: 'Hamed–Rao',
    raw: 'Anomalie mensuelle', deseasoned: 'Désaisonnalisée', trend: 'Tendance linéaire',
    guided: 'Parcours guidé', demo: 'Voir un exemple guidé', demoTitle: 'Exemples guidés',
    startDemo: 'Explorer cet exemple', next: 'Étape suivante', finish: 'Voir le résultat', close: 'Fermer',
    theme: 'Quel thème vous intéresse ?', themeClimate: 'Climat', themeWater: 'Eau',
    themePlants: 'Végétation', themeAir: 'Qualité de l’air', where: 'Où regarder ?',
    source: 'NASA GISS GISTEMP v4', unit: 'K / an', mapTitle: 'Carte mondiale des tendances',
    mapHelp: 'Le rose/rouge indique une tendance au réchauffement ; le bleu, un refroidissement. Les points marquent les mailles qui ne passent pas le seuil statistique. Cliquez sur une maille pour voir sa série.',
    noData: 'GISTEMP prétraité est indisponible. Lancez `make preprocess` pour le générer.',
    testConflict: 'Les tests simple et corrigé de l’autocorrélation diffèrent. Comparez les valeurs p et l’intervalle avant toute conclusion.',
    disclaimer: 'Une tendance significative indique une preuve statistique de changement, pas sa cause.',
    aboutTitle: 'Détective des tendances terrestres', aboutText: 'Un outil pédagogique pour explorer les observations NASA selon le lieu et la période.',
    data: 'Données et crédits', limitations: 'Limites', periodShort: 'période', coordinates: 'Maille sélectionnée',
    choose: 'Choisir',
    methodsIntro: 'L’outil distingue l’analyse régionale de la carte de repérage. Cliquez sur une région ou une maille pour afficher l’analyse complète.',
    m1: 'Les MCO ajustent une droite aux anomalies mensuelles désaisonnalisées. Le test t et l’intervalle à 95 % décrivent l’incertitude sous indépendance des résidus.',
    m2: 'Mann–Kendall teste si les valeurs évoluent dans une direction. La pente de Sen estime un taux robuste à partir des pentes entre paires.',
    m3: 'Hamed–Rao ajuste la variance Mann–Kendall à la dépendance temporelle. La carte utilise un test MCO rapide suivi de FDR Benjamini–Hochberg à 0,10.',
    validation: 'Validation avec la série mensuelle globale publiée par NASA : 561 mois (1980–2026), RMSE de 0,050 K ; les pentes mondiales diffèrent de moins de 0,000001 K/an.',
    mapWindow: 'Période de la carte',
    blankMap: 'Carte de tendance indisponible', point: 'Point', region: 'Région',
    dataFrequency: 'Mensuel · grille de 2°', fieldHelp: 'Choisissez une zone ou tracez-la sur la carte.',
    slopeLayer: 'Pente MCO · K/an', nonsignificantLayer: 'points = non significatif', observations: 'mois',
  },
} as const

const locale = ref<Locale>('en')
const t = computed(() => copy[locale.value])
const page = ref<AppPage>('explore')
const mapElement = ref<HTMLElement | null>(null)
const mapLayer = ref<MapLayer | null>(null)
const mapWindow = ref<WindowId>('full')
const variables = ref<VariableInfo[]>([])
const regions = ref<RegionInfo[]>([])
const regionId = ref('amazon')
const selectedBounds = ref<[number, number, number, number]>([-75, -15, -45, 5])
const selectedLabel = ref('Amazon example box')
const selectedPoint = ref<{ lat: number; lon: number } | null>(null)
const period = ref<WindowId>('full')
const analysis = ref<Analysis | null>(null)
const loading = ref(false)
const mapLoading = ref(false)
const error = ref('')
const showWizard = ref(true)
const wizardStep = ref(1)
const wizardTheme = ref('climate')
const wizardPlace = ref('Amazon')
const showDemos = ref(false)
const demoStep = ref(0)
const activeDemo = ref('')
const chartMode = ref<'anomaly' | 'raw'>('anomaly')

const periodStart: Record<WindowId, string | undefined> = {
  full: undefined,
  '2010-fin': '2010-01',
  '2015-fin': '2015-01',
}

const chartOption = computed(() => {
  if (!analysis.value) return {}
  const labels = analysis.value.time
  const raw = analysis.value.value
  const deseasoned = analysis.value.anomaly
  const series = chartMode.value === 'raw' ? raw : deseasoned
  const trend = analysis.value.trend.slope_ols
  const trendLine = fittedLine(series, trend)
  return {
    animation: false,
    color: chartMode.value === 'raw' ? ['#526071'] : ['#0b3d91', '#006a63'],
    grid: { left: 48, right: 18, top: 28, bottom: 32 },
    tooltip: { trigger: 'axis', valueFormatter: (value: number) => `${value.toFixed(3)} K` },
    xAxis: { type: 'category', boundaryGap: false, data: labels, axisLine: { lineStyle: { color: '#c4c6d3' } }, axisLabel: { color: '#526071', hideOverlap: true } },
    yAxis: { type: 'value', name: 'K', splitLine: { lineStyle: { color: '#e3e7ee' } }, axisLabel: { color: '#526071' } },
    series: [
      { name: chartMode.value === 'raw' ? t.value.raw : t.value.deseasoned, type: 'line', showSymbol: false, connectNulls: false, lineStyle: { width: 1.5 }, data: series },
      ...(chartMode.value === 'raw' ? [] : [{ name: t.value.trend, type: 'line', showSymbol: false, symbol: 'none', connectNulls: true, lineStyle: { color: '#006a63', width: 2, type: 'dashed' }, data: trendLine }]),
    ],
  }
})

const statusText = computed(() => {
  if (!analysis.value || analysis.value.trend.n_valid < 36) return t.value.insufficient
  return analysis.value.significant ? t.value.significant : t.value.notSignificant
})
const testConflict = computed(() => {
  const trend = analysis.value?.trend
  if (!trend || trend.p_value === null || trend.p_ols === null) return false
  return (trend.p_value < 0.05) !== (trend.p_ols < 0.05)
})

function periodBounds(bounds: [number, number, number, number]) {
  return bounds
}

async function loadMap() {
  mapLoading.value = true
  try {
    mapLayer.value = await api.map(mapWindow.value)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    mapLoading.value = false
  }
}

async function runAnalysis() {
  loading.value = true
  error.value = ''
  try {
    analysis.value = selectedPoint.value
      ? await api.point(
          selectedPoint.value.lat,
          selectedPoint.value.lon,
          periodStart[period.value],
        )
      : await api.region(
          periodBounds(selectedBounds.value), selectedLabel.value, periodStart[period.value],
        )
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    loading.value = false
  }
}

async function inspectPoint(lat: number, lon: number) {
  loading.value = true
  error.value = ''
  selectedPoint.value = { lat, lon }
  selectedLabel.value = `${lat.toFixed(1)}°, ${lon.toFixed(1)}°`
  try {
    analysis.value = await api.point(lat, lon, periodStart[period.value])
    regionId.value = ''
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    loading.value = false
  }
}

function chooseRegion(id: string) {
  regionId.value = id
  selectedPoint.value = null
  const selected = regions.value.find((item) => item.id === id)
  if (!selected) return
  selectedBounds.value = selected.bounds
  selectedLabel.value = locale.value === 'fr' ? selected.name_fr : selected.name
  void runAnalysis()
}

function chooseDrawnRegion(bounds: [number, number, number, number]) {
  regionId.value = ''
  selectedPoint.value = null
  selectedBounds.value = bounds
  selectedLabel.value = locale.value === 'fr' ? 'Région dessinée' : 'Drawn region'
  void runAnalysis()
}

function beginWizard() {
  wizardStep.value = 1
  showWizard.value = true
}

async function wizardNext() {
  if (wizardStep.value < 3) {
    wizardStep.value++
    return
  }
  showWizard.value = false
  const suggestions = await api.suggest(wizardTheme.value, wizardPlace.value)
  if (!suggestions[0]?.available) {
    error.value = suggestions[0]?.message ?? ''
    return
  }
  const match = regions.value.find((item) => `${item.name} ${item.name_fr}`.toLowerCase().includes(wizardPlace.value.toLowerCase()))
  if (match) chooseRegion(match.id)
}

async function startDemo(id: string) {
  activeDemo.value = id
  demoStep.value = 1
  showDemos.value = false
  period.value = 'full'
  const region = id === 'arctic' ? null : regions.value.find((item) => item.id === (id === 'sahara' ? 'sahara' : 'amazon'))
  if (region) {
    regionId.value = region.id
    selectedBounds.value = region.bounds
    selectedLabel.value = locale.value === 'fr' ? region.name_fr : region.name
  } else {
    selectedBounds.value = [-180, 70, 180, 90]
    selectedLabel.value = locale.value === 'fr' ? 'Arctique (70–90°N)' : 'Arctic (70–90°N)'
    regionId.value = ''
    selectedPoint.value = null
  }
  await runAnalysis()
  demoStep.value = 1
}

function stepDemo() {
  if (demoStep.value >= 3) {
    demoStep.value = 0
    activeDemo.value = ''
  } else {
    demoStep.value++
  }
}

const { drawing, startDrawing, cancelDrawing } = useMap(mapElement, mapLayer, inspectPoint, chooseDrawnRegion)

watch(period, () => {
  void runAnalysis()
})
watch(mapWindow, () => void loadMap())
watch(locale, () => {
  if (regionId.value) {
    const selected = regions.value.find((item) => item.id === regionId.value)
    if (selected) selectedLabel.value = locale.value === 'fr' ? selected.name_fr : selected.name
  }
})

onMounted(async () => {
  try {
    ;[variables.value, regions.value] = await Promise.all([api.variables(), api.regions()])
    await Promise.all([loadMap(), runAnalysis()])
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  }
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#explore" @click.prevent="page = 'explore'">
        <span class="brand-mark" aria-hidden="true">◎</span>
        <span class="brand-name">Earth Trend Detective</span>
        <span class="brand-tag">NASA EARTH SCIENCE</span>
      </a>
      <nav class="main-nav" aria-label="Main navigation">
        <button :class="{ active: page === 'explore' }" @click="page = 'explore'">{{ t.explore }}</button>
        <button :class="{ active: page === 'methods' }" @click="page = 'methods'">{{ t.methods }}</button>
        <button :class="{ active: page === 'about' }" @click="page = 'about'">{{ t.about }}</button>
      </nav>
      <div class="top-actions">
        <button class="language-toggle" :aria-label="`Switch language to ${t.lang}`" @click="locale = locale === 'en' ? 'fr' : 'en'">{{ locale.toUpperCase() }}</button>
        <button class="button secondary compact" @click="showDemos = true">▶ <span>{{ t.demo }}</span></button>
      </div>
    </header>

    <main v-if="page === 'explore'" class="workspace">
      <aside class="control-panel">
        <div class="panel-head">
          <div><span class="eyebrow">{{ t.parameters }}</span><span class="dataset-pill">GISTEMP v4</span></div>
          <button class="icon-button" :aria-label="t.guided" title="Guided investigation" @click="beginWizard">?</button>
        </div>
        <div class="panel-scroll">
          <section class="parameter-card">
            <span class="step-label">01 · {{ t.variable }}</span>
            <h1>{{ variables[0]?.[locale === 'en' ? 'name' : 'name_fr'] ?? 'Surface temperature anomaly' }}</h1>
            <p>{{ variables[0]?.[locale === 'en' ? 'definition' : 'definition_fr'] }}</p>
            <div class="metadata-row"><span>{{ t.dataFrequency }}</span><span>1880–2026</span></div>
          </section>

          <section class="parameter-card">
            <div class="section-title-line"><span class="step-label">02 · {{ t.place }}</span><button class="text-button" @click="beginWizard">{{ t.guided }}</button></div>
            <label class="field-label" for="region-select">{{ t.selectRegion }}</label>
            <select id="region-select" :value="regionId" @change="chooseRegion(($event.target as HTMLSelectElement).value)">
              <option v-for="item in regions" :key="item.id" :value="item.id">{{ locale === 'fr' ? item.name_fr : item.name }}</option>
              <option v-if="!regionId" value="">{{ selectedPoint ? t.point : locale === 'fr' ? 'Région dessinée' : 'Drawn region' }}</option>
            </select>
            <button class="button draw-button" :class="{ drawing }" @click="drawing ? cancelDrawing() : startDrawing()">
              <span aria-hidden="true">⌖</span>{{ drawing ? t.drawing : t.draw }}
            </button>
            <p class="field-help">{{ drawing ? t.drawing : t.fieldHelp }}</p>
            <div v-if="!regionId && !selectedPoint" class="coordinates-grid">
              <label>W<input v-model.number="selectedBounds[0]" type="number" min="-180" max="180" step="0.5" aria-label="West longitude" /></label>
              <label>S<input v-model.number="selectedBounds[1]" type="number" min="-90" max="90" step="0.5" aria-label="South latitude" /></label>
              <label>E<input v-model.number="selectedBounds[2]" type="number" min="-180" max="180" step="0.5" aria-label="East longitude" /></label>
              <label>N<input v-model.number="selectedBounds[3]" type="number" min="-90" max="90" step="0.5" aria-label="North latitude" /></label>
            </div>
          </section>

          <section class="parameter-card period-card">
            <span class="step-label">03 · {{ t.period }}</span>
            <div class="segmented period-options" role="group" :aria-label="t.period">
              <button :class="{ selected: period === 'full' }" @click="period = 'full'">{{ t.full }}</button>
              <button :class="{ selected: period === '2010-fin' }" @click="period = '2010-fin'">{{ t.since2010 }}</button>
              <button :class="{ selected: period === '2015-fin' }" @click="period = '2015-fin'">{{ t.since2015 }}</button>
            </div>
            <button class="button primary full-button" :disabled="loading" @click="runAnalysis">{{ loading ? t.loading : t.apply }}</button>
          </section>

          <section v-if="analysis" class="result-card">
            <div class="result-heading"><span class="step-label">{{ t.summary }}</span><span class="verdict" :class="analysis.significant ? 'good' : 'caution'" :title="t.significanceHelp" :aria-label="t.significanceHelp">{{ analysis.significant ? '✓' : '◷' }} {{ statusText }}</span></div>
            <div class="rate-value">{{ formatRate(analysis.trend.slope_ols) }}</div>
            <div class="rate-label">{{ t.rate }} <span class="info" :title="t.m1">ⓘ</span></div>
            <div class="confidence-row"><span>{{ t.confidence }} <span class="info" :title="t.confidenceHelp" :aria-label="t.confidenceHelp">ⓘ</span></span><strong>{{ formatRate(analysis.trend.slope_ols_lo) }} – {{ formatRate(analysis.trend.slope_ols_hi) }}</strong></div>
            <div class="test-grid">
              <div :title="`${t.pValueHelp} ${t.m1}`"><span>{{ t.ols }} ⓘ</span><strong>p {{ formatPValue(analysis.trend.p_ols) }}</strong></div>
              <div :title="`${t.pValueHelp} ${t.m2}`"><span>{{ t.mk }} ⓘ</span><strong>p {{ formatPValue(analysis.trend.p_mk) }}</strong></div>
            </div>
            <p v-if="testConflict" class="period-note conflict-note">{{ t.testConflict }}</p>
            <p class="plain-summary">{{ analysis.summary[locale] }}</p>
            <p v-if="!analysis.significant" class="period-note">{{ t.longerPeriod }}</p>
          </section>
          <div v-if="error" class="error-message" role="alert">{{ error }} <button class="text-button" @click="error = ''">×</button></div>
        </div>
        <footer class="panel-footer"><span class="source-dot"></span>{{ t.source }} <a href="https://data.giss.nasa.gov/gistemp/" target="_blank" rel="noreferrer">↗</a></footer>
      </aside>

      <section class="map-workspace" aria-label="Trend map and time series">
        <div class="map-heading">
          <div><span class="eyebrow">{{ t.mapTitle }}</span><p>{{ t.mapHelp }}</p></div>
          <label class="map-period"><span>{{ t.mapWindow }}</span><select v-model="mapWindow"><option value="full">{{ t.full }}</option><option value="2010-fin">{{ t.since2010 }}</option><option value="2015-fin">{{ t.since2015 }}</option></select></label>
        </div>
        <div ref="mapElement" class="map-canvas" :aria-label="t.mapTitle"></div>
        <div class="map-overlay-label"><span class="overlay-swatch"></span>{{ t.slopeLayer }} <span class="subtle-separator">|</span> {{ t.nonsignificantLayer }}</div>
        <div class="map-legend" aria-label="Diverging trend palette legend"><span>{{ mapLayer?.scale_min.toFixed(3) ?? '−' }}</span><div class="legend-gradient"></div><span>0</span><span class="legend-gradient reverse"></span><span>+{{ Math.abs(mapLayer?.scale_max ?? 0).toFixed(3) }}</span><small>K/year</small></div>
        <div v-if="mapLoading" class="map-loading">{{ t.loadingMap }}</div>
        <div class="map-attribution">Basemap: NASA GIBS Blue Marble. Trend overlay: NASA GISS GISTEMP.</div>

        <section v-if="analysis" class="chart-panel">
          <div class="chart-header">
            <div><span class="eyebrow">{{ t.chart }}</span><h2>{{ selectedLabel }}</h2></div>
            <div class="segmented chart-toggle"><button :class="{ selected: chartMode === 'anomaly' }" @click="chartMode = 'anomaly'">{{ t.deseasoned }}</button><button :class="{ selected: chartMode === 'raw' }" @click="chartMode = 'raw'">{{ t.raw }}</button></div>
          </div>
          <VChart class="chart" :option="chartOption" autoresize aria-label="Monthly temperature anomaly time series" />
          <div class="chart-footnote">{{ analysis.period.start }} — {{ analysis.period.end }} · {{ analysis.trend.n_valid }} {{ t.observations }} · {{ t.disclaimer }}</div>
        </section>
      </section>
    </main>

    <main v-else-if="page === 'methods'" class="content-page">
      <div class="content-heading"><span class="eyebrow">SCIENTIFIC TRANSPARENCY</span><h1>{{ t.methods }}</h1><p>{{ t.methodsIntro }}</p></div>
      <div class="method-grid">
        <article><span class="method-index">01</span><h2>{{ t.ols }}</h2><p>{{ t.m1 }}</p><span class="method-formula">y = a + bt · b in K/year · 95% CI</span></article>
        <article><span class="method-index">02</span><h2>{{ t.mk }} + Sen</h2><p>{{ t.m2 }}</p><span class="method-formula">Median of pairwise slopes</span></article>
        <article><span class="method-index">03</span><h2>{{ t.hr }} + FDR</h2><p>{{ t.m3 }}</p><span class="method-formula">BH false discovery rate · α = 0.10</span></article>
      </div>
      <article class="validation-card"><span class="eyebrow">{{ t.validation }}</span><p>{{ t.validation }}</p><a href="https://data.giss.nasa.gov/gistemp/data_v4.html" target="_blank" rel="noreferrer">NASA GISTEMP v4 data and methods ↗</a></article>
      <article class="validation-card"><h2>{{ t.limitations }}</h2><p>{{ variables[0]?.limitations }}</p><p>{{ t.disclaimer }}</p></article>
    </main>

    <main v-else class="content-page about-page">
      <span class="brand-mark large" aria-hidden="true">◎</span><h1>{{ t.aboutTitle }}</h1><p>{{ t.aboutText }}</p>
      <section class="validation-card"><h2>{{ t.data }}</h2><p>NASA GISS GISTEMP v4 · Land–Ocean Temperature Index · ERSSTv5 · 2° grid.</p><a href="https://data.giss.nasa.gov/gistemp/" target="_blank" rel="noreferrer">NASA GISS GISTEMP ↗</a><p>Lenssen et al. (2024), DOI: 10.1029/2023JD040179.</p></section>
    </main>

    <div v-if="showWizard" class="modal-backdrop" role="presentation" @click.self="showWizard = false">
      <section class="dialog wizard-dialog" role="dialog" aria-modal="true" aria-labelledby="wizard-title">
        <div class="dialog-top"><span class="eyebrow">{{ t.guided }}</span><button class="icon-button" :aria-label="t.close" @click="showWizard = false">×</button></div>
        <div class="wizard-progress"><span v-for="step in 3" :key="step" :class="{ filled: step <= wizardStep }"></span></div>
        <span class="step-label">{{ locale === 'en' ? 'STEP' : 'ÉTAPE' }} {{ wizardStep }} / 3</span>
        <template v-if="wizardStep === 1"><h2 id="wizard-title">{{ t.theme }}</h2><div class="choice-grid"><button v-for="choice in [['climate', t.themeClimate], ['water', t.themeWater], ['vegetation', t.themePlants], ['air', t.themeAir]]" :key="choice[0]" :class="{ chosen: wizardTheme === choice[0] }" @click="wizardTheme = choice[0]">{{ choice[1] }}</button></div></template>
        <template v-else-if="wizardStep === 2"><h2 id="wizard-title">{{ t.where }}</h2><label class="field-label" for="wizard-place">{{ t.place }}</label><input id="wizard-place" v-model="wizardPlace" class="text-input" placeholder="e.g. Amazon" /><div class="quick-places"><button v-for="region in regions" :key="region.id" @click="wizardPlace = locale === 'fr' ? region.name_fr : region.name">{{ locale === 'fr' ? region.name_fr : region.name }}</button></div></template>
        <template v-else><h2 id="wizard-title">{{ t.variable }}</h2><div class="wizard-variable"><strong>{{ variables[0]?.[locale === 'en' ? 'name' : 'name_fr'] }}</strong><p>{{ variables[0]?.[locale === 'en' ? 'definition' : 'definition_fr'] }}</p><span>NASA GISS · monthly · 2° grid</span></div></template>
        <div class="dialog-actions"><button class="button secondary" :disabled="wizardStep === 1" @click="wizardStep--">{{ locale === 'en' ? 'Back' : 'Retour' }}</button><button class="button primary" @click="wizardNext">{{ wizardStep === 3 ? t.apply : locale === 'en' ? 'Continue' : 'Continuer' }} <span aria-hidden="true">→</span></button></div>
      </section>
    </div>

    <div v-if="showDemos" class="modal-backdrop" role="presentation" @click.self="showDemos = false">
      <section class="dialog demos-dialog" role="dialog" aria-modal="true" aria-labelledby="demos-title">
        <div class="dialog-top"><div><span class="eyebrow">{{ t.guided }}</span><h2 id="demos-title">{{ t.demoTitle }}</h2></div><button class="icon-button" :aria-label="t.close" @click="showDemos = false">×</button></div>
        <button class="demo-option" @click="startDemo('arctic')"><span class="demo-number">01</span><span><strong>{{ locale === 'en' ? 'Arctic amplification' : 'Amplification arctique' }}</strong><small>70–90°N · GISTEMP v4 · full record</small></span><span>→</span></button>
        <button class="demo-option" @click="startDemo('amazon')"><span class="demo-number">02</span><span><strong>{{ locale === 'en' ? 'Tropical forest region' : 'Forêt tropicale' }}</strong><small>Amazon example area · GISTEMP v4</small></span><span>→</span></button>
        <p class="dialog-note">{{ locale === 'en' ? 'All example series use the NASA GISTEMP v4 record:' : 'Toutes les séries d’exemple utilisent les données NASA GISTEMP v4 :' }} <a href="https://data.giss.nasa.gov/gistemp/" target="_blank" rel="noreferrer">NASA GISS</a>. {{ locale === 'en' ? 'Arctic context:' : 'Contexte arctique :' }} <a href="https://doi.org/10.1029/2021GL094086" target="_blank" rel="noreferrer">England et al. (2021)</a>.</p>
      </section>
    </div>

    <div v-if="activeDemo && demoStep" class="demo-callout" role="status">
      <div><span class="eyebrow">GUIDED EXAMPLE · {{ demoStep }}/3</span><strong>{{ selectedLabel }}</strong><p v-if="demoStep === 2">{{ locale === 'en' ? 'The regional series is ready. The chart separates monthly anomalies from the seasonal cycle.' : 'La série est prête. Le graphique sépare les anomalies du cycle saisonnier.' }}</p><p v-else-if="demoStep === 3">{{ analysis?.summary[locale] }}</p><p v-else>{{ locale === 'en' ? 'The example region and complete GISTEMP record are selected.' : 'La région et toute la série GISTEMP sont sélectionnées.' }}</p></div>
      <button class="button primary" @click="stepDemo">{{ demoStep === 3 ? t.finish : t.next }}</button>
    </div>
  </div>
</template>
