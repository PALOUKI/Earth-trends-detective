<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { Analysis, Comparison, MapLayer, RegionInfo, VariableInfo } from './api'
import { api } from './api'
import { fittedLine, formatPValue, formatRate } from './trendUtils'
import { useMap } from './useMap'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

type Locale = 'en' | 'fr'
type WindowId = 'full' | '2010-fin' | '2015-fin'
type AppPage = 'home' | 'explore' | 'variables' | 'compare' | 'methods' | 'about'

const copy = {
  en: {
    home: 'Home', variablesPage: 'Variables', comparePage: 'Compare',
    homeTitle: 'Find out what is changing on Earth',
    homeLead: 'Choose a NASA Earth science variable and a place. Explore its monthly record, estimate the rate of change, and check the statistical evidence.',
    startInvestigation: 'Start an investigation', browseVariables: 'Browse verified variables',
    howTitle: 'From question to evidence', howChoose: 'Choose a measured variable',
    howRegion: 'Select a region', howAnalyze: 'Inspect the time series and trend tests',
    inventory: 'Verified data inventory', readyDatasets: 'analysis-ready datasets',
    processingDatasets: 'in progress', variableSearch: 'Search verified variables', allStatuses: 'All statuses',
    readyStatus: 'Analysis ready', compareTitle: 'Compare two regions',
    loadingVariables: 'Loading analysis-ready variables…', noAvailableVariables: 'The API has not returned any analysis-ready variables.',
    compareIntro: 'Use the same available variable and full record for both regions. Results are calculated from their actual processed series.',
    regionA: 'Region A', regionB: 'Region B', runCompare: 'Compare regions', rateA: 'Region A rate', rateB: 'Region B rate',
    compareCaveat: 'Differences describe the selected regional averages. They do not establish a cause.',
    exportTitle: 'Export real analysis products', exportCSV: 'Regional monthly series (CSV)',
    exportPNG: 'Precomputed trend map (PNG)', exportTIF: 'Trend grid (GeoTIFF)',
    exportNote: 'Exports use the selected processed dataset. Map files are available only when generated.',
    notOfficial: 'Independent project; not an official NASA product.',
    explore: 'Explore', methods: 'Methods & validation', about: 'About', lang: 'Français',
    parameters: 'Analysis parameters', dataset: 'DATASET', variable: 'Variable',
    accessBlocked: 'Access authorization pending', sampleOnly: 'Sample acquired; trend analysis pending',
    acquiring: 'Downloading granules; analysis pending', seriesProcessed: 'Time series processed; maps pending',
    qualityPending: 'NASA OMI air-quality observations are still downloading. The 2005–2014 monthly series and trend maps are not ready yet.',
    variablePending: 'This NASA dataset is still being prepared and cannot be analyzed yet.',
    place: 'Study area', selectRegion: 'Choose a region', draw: 'Draw a rectangle',
    drawing: 'Drag on the map to draw', period: 'Analysis period', full: 'Full record',
    since2010: 'Since 2010', since2015: 'Since 2015', apply: 'Analyze region',
    chart: 'Regional time series', summary: 'Trend summary', loading: 'Analyzing selected variable…',
    loadingMap: 'Loading trend layer…', rate: 'Linear rate', confidence: '95% confidence interval',
    pValueHelp: 'A p-value measures how unusual these data would be if there were no trend; it is not the probability that the result is true.',
    confidenceHelp: 'The 95% interval gives a range of plausible linear rates under the model assumptions.',
    significanceHelp: 'This label compares the OLS p-value with 0.05. It does not identify a cause.',
    significant: 'Significant', notSignificant: 'Not (yet) significant', insufficient: 'Not enough data',
    longerPeriod: 'A longer time period could change this significance result.',
    ols: 'OLS t test', mk: 'Mann–Kendall', hr: 'Hamed–Rao',
    raw: 'Monthly values', deseasoned: 'Deseasonalized', trend: 'Linear trend',
    guided: 'Guided investigation', demo: 'Try a guided example', demoTitle: 'Guided examples',
    startDemo: 'Explore example', next: 'Next step', finish: 'Show result', close: 'Close',
    theme: 'What interests you?', themeClimate: 'Climate', themeWater: 'Water',
    themePlants: 'Vegetation', themeAir: 'Air quality', where: 'Where should we look?',
    source: 'NASA GISS GISTEMP v4', unit: 'K / year', mapTitle: 'Global trend discovery map',
    mapHelp: 'Red cells show positive trends and blue shows negative trends. Dots mark cells that did not pass the map significance threshold. Click a cell to inspect its series.',
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
    slopeLayer: 'OLS slope', nonsignificantLayer: 'dots = not significant', observations: 'months',
  },
  fr: {
    home: 'Accueil', variablesPage: 'Variables', comparePage: 'Comparer',
    homeTitle: 'Découvrir ce qui change sur Terre',
    homeLead: 'Choisissez une variable NASA et un lieu. Explorez sa série mensuelle, estimez le rythme de changement et consultez les tests statistiques.',
    startInvestigation: 'Commencer une enquête', browseVariables: 'Voir les variables vérifiées',
    howTitle: 'De la question aux résultats', howChoose: 'Choisir une variable mesurée',
    howRegion: 'Sélectionner une région', howAnalyze: 'Examiner la série et les tests de tendance',
    inventory: 'Catalogue réel des données', readyDatasets: 'variables analysables',
    processingDatasets: 'en cours', variableSearch: 'Rechercher une variable vérifiée', allStatuses: 'Tous les états',
    readyStatus: 'Analyse disponible', compareTitle: 'Comparer deux régions',
    loadingVariables: 'Chargement des variables analysables…', noAvailableVariables: 'L’API n’a renvoyé aucune variable analysable.',
    compareIntro: 'Une même variable et toute la période disponible sont utilisées dans les deux régions. Les résultats sont calculés à partir des séries traitées.',
    regionA: 'Région A', regionB: 'Région B', runCompare: 'Comparer les régions', rateA: 'Taux région A', rateB: 'Taux région B',
    compareCaveat: 'Les différences décrivent les moyennes régionales choisies ; elles ne démontrent pas une cause.',
    exportTitle: 'Exporter les résultats calculés', exportCSV: 'Série mensuelle régionale (CSV)',
    exportPNG: 'Carte de tendance précalculée (PNG)', exportTIF: 'Grille de tendance (GeoTIFF)',
    exportNote: 'Les exports utilisent les données traitées sélectionnées. Les cartes sont disponibles uniquement si elles ont été générées.',
    notOfficial: 'Projet indépendant ; ce n’est pas un produit officiel de la NASA.',
    explore: 'Explorer', methods: 'Méthodes et validation', about: 'À propos', lang: 'English',
    parameters: 'Paramètres d’analyse', dataset: 'JEU DE DONNÉES', variable: 'Variable',
    accessBlocked: 'Autorisation d’accès en attente', sampleOnly: 'Échantillon acquis ; analyse en attente',
    acquiring: 'Granules en téléchargement ; analyse en attente', seriesProcessed: 'Série prétraitée ; cartes en attente',
    qualityPending: 'Les observations NASA OMI sur la qualité de l’air sont encore en téléchargement. La série mensuelle 2005–2014 et ses cartes de tendance ne sont pas encore prêtes.',
    variablePending: 'Ce jeu de données NASA est encore en préparation et ne peut pas encore être analysé.',
    place: 'Zone étudiée', selectRegion: 'Choisir une région', draw: 'Dessiner un rectangle',
    drawing: 'Tracer sur la carte', period: 'Période d’analyse', full: 'Toute la série',
    since2010: 'Depuis 2010', since2015: 'Depuis 2015', apply: 'Analyser la région',
    chart: 'Série temporelle régionale', summary: 'Résumé de tendance', loading: 'Analyse de la variable…',
    loadingMap: 'Chargement de la carte…', rate: 'Taux linéaire', confidence: 'Intervalle de confiance à 95 %',
    pValueHelp: 'La valeur p indique à quel point ces données seraient inhabituelles en l’absence de tendance ; ce n’est pas la probabilité que le résultat soit vrai.',
    confidenceHelp: 'L’intervalle à 95 % donne une plage de taux linéaires plausibles sous les hypothèses du modèle.',
    significanceHelp: 'Cette étiquette compare la valeur p MCO au seuil de 0,05. Elle ne donne pas la cause.',
    significant: 'Significative', notSignificant: 'Pas (encore) significative', insufficient: 'Données insuffisantes',
    longerPeriod: 'Une période plus longue pourrait changer ce résultat de significativité.',
    ols: 'Test t MCO', mk: 'Mann–Kendall', hr: 'Hamed–Rao',
    raw: 'Valeurs mensuelles', deseasoned: 'Désaisonnalisée', trend: 'Tendance linéaire',
    guided: 'Parcours guidé', demo: 'Voir un exemple guidé', demoTitle: 'Exemples guidés',
    startDemo: 'Explorer cet exemple', next: 'Étape suivante', finish: 'Voir le résultat', close: 'Fermer',
    theme: 'Quel thème vous intéresse ?', themeClimate: 'Climat', themeWater: 'Eau',
    themePlants: 'Végétation', themeAir: 'Qualité de l’air', where: 'Où regarder ?',
    source: 'NASA GISS GISTEMP v4', unit: 'K / an', mapTitle: 'Carte mondiale des tendances',
    mapHelp: 'Le rouge indique une tendance positive et le bleu une tendance négative. Les points marquent les mailles qui ne passent pas le seuil statistique. Cliquez sur une maille pour voir sa série.',
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
    slopeLayer: 'Pente MCO', nonsignificantLayer: 'points = non significatif', observations: 'mois',
  },
} as const

const locale = ref<Locale>('fr')
const t = computed(() => copy[locale.value])
const page = ref<AppPage>('home')
const mapElement = ref<HTMLElement | null>(null)
const mapLayer = ref<MapLayer | null>(null)
const mapWindow = ref<WindowId>('full')
const variables = ref<VariableInfo[]>([])
const catalogVariables = ref<VariableInfo[]>([])
// /api/variables already filters to analysis-ready records; its response schema
// intentionally omits catalog-only fields such as `status`.
const readyVariables = computed(() => variables.value.length
  ? variables.value
  : catalogVariables.value.filter((item) => item.status === 'analysis_ready'))
const inventoryLoading = ref(true)
const catalogSearch = ref('')
const catalogStatus = ref('all')
const selectedVariable = ref('gistemp_tas_anom')
const wizardTheme = ref('climate')
const activeVariable = computed(() => catalogVariables.value.find((item) => item.id === selectedVariable.value)
  ?? readyVariables.value.find((item) => item.id === selectedVariable.value)
  ?? readyVariables.value[0])
const wizardVariableId = computed(() => ({
  climate: 'gistemp_tas_anom', water: 'gpm_precipitation', vegetation: 'modis_ndvi',
  air: 'omi_no2',
}[wizardTheme.value] ?? 'gistemp_tas_anom'))
const wizardVariable = computed(() => catalogVariables.value.find((item) => item.id === wizardVariableId.value) ?? variables.value[0])
const wizardVariableReady = computed(() => variables.value.some((item) => item.id === wizardVariableId.value))
const isAnalysisReady = computed(() => readyVariables.value.some((item) => item.id === selectedVariable.value))
const filteredCatalog = computed(() => catalogVariables.value.filter((item) => {
  const query = catalogSearch.value.toLowerCase()
  const matchesText = `${item.name} ${item.name_fr} ${item.source ?? ''} ${item.short_name ?? ''}`.toLowerCase().includes(query)
  return matchesText && (catalogStatus.value === 'all' || item.status === catalogStatus.value)
}))
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
const comparing = ref(false)
const comparison = ref<Comparison | null>(null)
const compareA = ref('amazon')
const compareB = ref('sahara')
const showExport = ref(false)
const showWizard = ref(false)
const wizardStep = ref(1)
const wizardPlace = ref('Amazon')
const showDemos = ref(false)
const demoStep = ref(0)
const activeDemo = ref('')
const chartMode = ref<'anomaly' | 'raw'>('anomaly')

const comparisonOptionA = computed(() => comparison.value ? comparisonChartOption(comparison.value.a) : {})
const comparisonOptionB = computed(() => comparison.value ? comparisonChartOption(comparison.value.b) : {})
const regionalCsvUrl = computed(() => api.exportUrl({
  variable: selectedVariable.value, format: 'csv', bounds: selectedBounds.value,
}))
const slopePngUrl = computed(() => api.exportUrl({
  variable: selectedVariable.value, format: 'png', window: mapWindow.value, layer: 'slope',
}))
const trendTifUrl = computed(() => api.exportUrl({
  variable: selectedVariable.value, format: 'tif', window: mapWindow.value,
}))

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
    tooltip: { trigger: 'axis', valueFormatter: (value: number) => `${value.toFixed(3)} ${analysis.value?.unit ?? ''}` },
    xAxis: { type: 'category', boundaryGap: false, data: labels, axisLine: { lineStyle: { color: '#c4c6d3' } }, axisLabel: { color: '#526071', hideOverlap: true } },
    yAxis: { type: 'value', name: analysis.value.unit, splitLine: { lineStyle: { color: '#e3e7ee' } }, axisLabel: { color: '#526071' } },
    series: [
      { name: chartMode.value === 'raw' ? t.value.raw : t.value.deseasoned, type: 'line', showSymbol: false, connectNulls: false, lineStyle: { width: 1.5 }, data: series },
      ...(chartMode.value === 'raw' ? [] : [{ name: t.value.trend, type: 'line', showSymbol: false, symbol: 'none', connectNulls: true, lineStyle: { color: '#006a63', width: 2, type: 'dashed' }, data: trendLine }]),
    ],
  }
})

function comparisonChartOption(result: Analysis) {
  return {
    animation: false,
    color: ['#0b3d91'],
    grid: { left: 45, right: 12, top: 18, bottom: 28 },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: result.time, axisLabel: { hideOverlap: true } },
    yAxis: { type: 'value', name: result.unit },
    series: [{ type: 'line', showSymbol: false, connectNulls: false, data: result.anomaly }],
  }
}

async function runComparison() {
  if (!readyVariables.value.some((item) => item.id === selectedVariable.value)) {
    error.value = t.value.noAvailableVariables
    return
  }
  if (compareA.value === compareB.value) {
    error.value = locale.value === 'fr' ? 'Choisissez deux régions différentes.' : 'Choose two different regions.'
    return
  }
  comparing.value = true
  comparison.value = null
  error.value = ''
  try {
    comparison.value = await api.compare(selectedVariable.value, compareA.value, compareB.value)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    comparing.value = false
  }
}

function openVariable(variable: string) {
  const item = catalogVariables.value.find((candidate) => candidate.id === variable)
  if (!item) return
  if (item.status !== 'analysis_ready') {
    error.value = item.id === 'omi_no2' ? t.value.qualityPending : item.status_detail ?? t.value.variablePending
    return
  }
  selectedVariable.value = variable
  page.value = 'explore'
}

function statusLabel(status?: string) {
  const english: Record<string, string> = {
    analysis_ready: 'Analysis ready', sample_downloaded: 'Sample only',
    acquiring: 'Acquiring data', series_processed: 'Preparing maps', blocked_eula: 'Access pending',
  }
  const french: Record<string, string> = {
    analysis_ready: 'Analyse disponible', sample_downloaded: 'Échantillon seulement',
    acquiring: 'Acquisition en cours', series_processed: 'Cartes à préparer', blocked_eula: 'Accès en attente',
  }
  return (locale.value === 'fr' ? french : english)[status ?? ''] ?? status ?? ''
}

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
  if (!isAnalysisReady.value) {
    mapLayer.value = null
    mapLoading.value = false
    return
  }
  mapLoading.value = true
  try {
    mapLayer.value = await api.map(selectedVariable.value, mapWindow.value)
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    mapLoading.value = false
  }
}

async function runAnalysis() {
  if (!isAnalysisReady.value) {
    analysis.value = null
    return
  }
  loading.value = true
  error.value = ''
  try {
    analysis.value = selectedPoint.value
      ? await api.point(
          selectedVariable.value,
          selectedPoint.value.lat,
          selectedPoint.value.lon,
          periodStart[period.value],
        )
      : await api.region(
          selectedVariable.value, periodBounds(selectedBounds.value), selectedLabel.value, periodStart[period.value],
        )
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught)
  } finally {
    loading.value = false
  }
}

async function inspectPoint(lat: number, lon: number) {
  if (!isAnalysisReady.value) return
  loading.value = true
  error.value = ''
  selectedPoint.value = { lat, lon }
  selectedLabel.value = `${lat.toFixed(1)}°, ${lon.toFixed(1)}°`
  try {
    analysis.value = await api.point(selectedVariable.value, lat, lon, periodStart[period.value])
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
    error.value = suggestions[0]?.variable === 'omi_no2'
      ? t.value.qualityPending
      : suggestions[0]?.message ?? ''
    return
  }
  if (suggestions[0]?.variable) selectedVariable.value = suggestions[0].variable
  const match = regions.value.find((item) => `${item.name} ${item.name_fr}`.toLowerCase().includes(wizardPlace.value.toLowerCase()))
  if (match) chooseRegion(match.id)
}

async function startDemo(id: string) {
  selectedVariable.value = 'gistemp_tas_anom'
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
watch(selectedVariable, () => {
  selectedPoint.value = null
  mapWindow.value = 'full'
  if (isAnalysisReady.value) {
    void loadMap()
    void runAnalysis()
  } else {
    mapLayer.value = null
    analysis.value = null
    error.value = ''
  }
})
watch(locale, () => {
  if (regionId.value) {
    const selected = regions.value.find((item) => item.id === regionId.value)
    if (selected) selectedLabel.value = locale.value === 'fr' ? selected.name_fr : selected.name
  }
})

onMounted(async () => {
  const results = await Promise.allSettled([api.variables(), api.catalog(), api.regions()])
  if (results[0].status === 'fulfilled') variables.value = results[0].value
  if (results[1].status === 'fulfilled') catalogVariables.value = results[1].value
  if (results[2].status === 'fulfilled') regions.value = results[2].value
  inventoryLoading.value = false
  const failed = results.find((result) => result.status === 'rejected')
  if (failed?.status === 'rejected' && !readyVariables.value.length) {
    error.value = failed.reason instanceof Error ? failed.reason.message : String(failed.reason)
  }
  await Promise.all([loadMap(), runAnalysis()])
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <a class="brand" href="#home" @click.prevent="page = 'home'">
        <span class="brand-mark" aria-hidden="true">◎</span>
        <span class="brand-name">Earth Trend Detective</span>
        <span class="brand-tag">NASA EARTH SCIENCE</span>
      </a>
      <nav class="main-nav" aria-label="Main navigation">
        <button :class="{ active: page === 'home' }" @click="page = 'home'">{{ t.home }}</button>
        <button :class="{ active: page === 'explore' }" @click="page = 'explore'">{{ t.explore }}</button>
        <button :class="{ active: page === 'variables' }" @click="page = 'variables'">{{ t.variablesPage }}</button>
        <button :class="{ active: page === 'compare' }" @click="page = 'compare'">{{ t.comparePage }}</button>
        <button :class="{ active: page === 'methods' }" @click="page = 'methods'">{{ t.methods }}</button>
        <button :class="{ active: page === 'about' }" @click="page = 'about'">{{ t.about }}</button>
      </nav>
      <div class="top-actions">
        <button class="language-toggle" :aria-label="`Switch language to ${t.lang}`" @click="locale = locale === 'en' ? 'fr' : 'en'">{{ locale.toUpperCase() }}</button>
        <button v-if="page === 'explore' && isAnalysisReady" class="button secondary compact" @click="showExport = true">↓ <span>Export</span></button>
        <button class="button secondary compact" @click="showDemos = true">▶ <span>{{ t.demo }}</span></button>
      </div>
    </header>

    <main v-if="page === 'home'" class="home-page">
      <section class="landing-hero">
        <span class="eyebrow">NASA EARTH SCIENCE · DATA TRENDS</span>
        <h1>{{ t.homeTitle }}</h1>
        <p>{{ t.homeLead }}</p>
        <div class="landing-actions">
          <button class="button primary" @click="page = 'explore'; beginWizard()">{{ t.startInvestigation }} →</button>
          <button class="button secondary" @click="page = 'variables'">{{ t.browseVariables }}</button>
        </div>
        <div class="landing-inventory" aria-live="polite">
          <strong>{{ readyVariables.length }}</strong><span>{{ t.readyDatasets }}</span>
          <i></i><strong>{{ catalogVariables.filter((item) => item.status !== 'analysis_ready').length }}</strong><span>{{ t.processingDatasets }}</span>
        </div>
      </section>
      <section class="landing-section">
        <div class="section-heading"><span class="eyebrow">{{ t.howTitle }}</span><button class="text-button" @click="page = 'methods'">{{ t.methods }} →</button></div>
        <div class="landing-steps">
          <article><span class="method-index">01</span><h2>{{ t.howChoose }}</h2><p>{{ locale === 'fr' ? 'Les jeux NASA sont listés avec leur source, période, unité et état d’intégration.' : 'NASA datasets are listed with source, period, unit, and integration status.' }}</p></article>
          <article><span class="method-index">02</span><h2>{{ t.howRegion }}</h2><p>{{ locale === 'fr' ? 'Choisissez une région prédéfinie ou dessinez une emprise sur la carte.' : 'Choose a predefined region or draw an area on the map.' }}</p></article>
          <article><span class="method-index">03</span><h2>{{ t.howAnalyze }}</h2><p>{{ locale === 'fr' ? 'Consultez la pente, l’intervalle de confiance et les tests de significativité.' : 'Review the slope, confidence interval, and significance tests.' }}</p></article>
        </div>
      </section>
      <section class="landing-section ready-section">
        <div class="section-heading"><div><span class="eyebrow">{{ t.inventory }}</span><h2>{{ locale === 'fr' ? 'Variables réellement intégrées' : 'Datasets actually integrated' }}</h2></div><button class="button secondary compact" @click="page = 'variables'">{{ t.variablesPage }} →</button></div>
        <div class="ready-chips"><button v-for="item in readyVariables" :key="item.id" @click="openVariable(item.id)">{{ locale === 'fr' ? item.name_fr : item.name }} <span>· {{ item.unit }}</span></button></div>
      </section>
      <footer class="landing-disclaimer"><span>ⓘ</span><p>{{ t.notOfficial }} {{ t.disclaimer }}</p></footer>
    </main>

    <main v-else-if="page === 'variables'" class="content-page catalog-page">
      <div class="content-heading"><span class="eyebrow">{{ t.inventory }}</span><h1>{{ locale === 'fr' ? 'Variables de sciences de la Terre' : 'Earth science variables' }}</h1><p>{{ locale === 'fr' ? 'Ce catalogue est alimenté par les enregistrements de données du projet. Les jeux en cours d’acquisition restent indisponibles pour l’analyse.' : 'This catalogue is populated from the project data records. Datasets still being acquired cannot yet be analyzed.' }}</p></div>
      <div class="catalog-controls"><input v-model="catalogSearch" class="text-input" type="search" :placeholder="t.variableSearch" /><select v-model="catalogStatus" :aria-label="t.allStatuses"><option value="all">{{ t.allStatuses }}</option><option value="analysis_ready">{{ t.readyStatus }}</option><option value="acquiring">{{ statusLabel('acquiring') }}</option><option value="sample_downloaded">{{ statusLabel('sample_downloaded') }}</option><option value="series_processed">{{ statusLabel('series_processed') }}</option><option value="blocked_eula">{{ statusLabel('blocked_eula') }}</option></select></div>
      <div class="catalog-grid">
        <article v-for="item in filteredCatalog" :key="item.id" class="catalog-card">
          <div class="catalog-card-top"><span class="eyebrow">{{ item.short_name ?? item.source }}</span><span class="status-badge" :class="item.status === 'analysis_ready' ? 'status-ready' : 'status-pending'">{{ statusLabel(item.status) }}</span></div>
          <h2>{{ locale === 'fr' ? item.name_fr : item.name }}</h2><p>{{ locale === 'fr' ? item.definition_fr : item.definition }}</p>
          <dl><div><dt>{{ locale === 'fr' ? 'Période' : 'Period' }}</dt><dd>{{ item.period }}</dd></div><div><dt>{{ locale === 'fr' ? 'Unité' : 'Unit' }}</dt><dd>{{ item.unit }}</dd></div><div><dt>{{ locale === 'fr' ? 'Source' : 'Source' }}</dt><dd>{{ item.source }}</dd></div></dl>
          <p v-if="item.status !== 'analysis_ready'" class="catalog-pending">{{ item.id === 'omi_no2' ? t.qualityPending : item.status_detail }}</p>
          <div class="catalog-actions"><a v-if="item.doi" :href="`https://doi.org/${item.doi}`" target="_blank" rel="noreferrer">DOI ↗</a><button class="button compact" :class="item.status === 'analysis_ready' ? 'primary' : 'secondary'" :disabled="item.status !== 'analysis_ready'" @click="openVariable(item.id)">{{ item.status === 'analysis_ready' ? t.explore : statusLabel(item.status) }}</button></div>
        </article>
        <p v-if="filteredCatalog.length === 0" class="empty-catalog">{{ locale === 'fr' ? 'Aucune variable ne correspond à cette recherche.' : 'No variables match this search.' }}</p>
      </div>
    </main>

    <main v-else-if="page === 'compare'" class="content-page compare-page">
      <div class="content-heading"><span class="eyebrow">{{ t.comparePage }}</span><h1>{{ t.compareTitle }}</h1><p>{{ t.compareIntro }}</p></div>
      <div v-if="error" class="error-message compare-error" role="alert">{{ error }} <button class="text-button" :aria-label="t.close" :title="t.close" @click="error = ''">×</button></div>
      <div class="compare-controls">
        <label>{{ t.variable }}<select v-model="selectedVariable"><option v-for="item in readyVariables" :key="item.id" :value="item.id">{{ locale === 'fr' ? item.name_fr : item.name }}</option></select></label>
        <label>{{ t.regionA }}<select v-model="compareA"><option v-for="item in regions" :key="item.id" :value="item.id">{{ locale === 'fr' ? item.name_fr : item.name }}</option></select></label>
        <label>{{ t.regionB }}<select v-model="compareB"><option v-for="item in regions" :key="item.id" :value="item.id">{{ locale === 'fr' ? item.name_fr : item.name }}</option></select></label>
        <button class="button primary" :disabled="comparing || !readyVariables.length" @click="runComparison">{{ comparing ? t.loading : t.runCompare }}</button>
      </div>
      <p v-if="inventoryLoading" class="empty-catalog" role="status">{{ t.loadingVariables }}</p>
      <p v-else-if="!readyVariables.length" class="empty-catalog" role="status">{{ t.noAvailableVariables }} {{ error }}</p>
      <div v-if="comparison" class="comparison-grid">
        <article v-for="(result, index) in [comparison.a, comparison.b]" :key="index" class="comparison-card">
          <span class="eyebrow">{{ index === 0 ? t.regionA : t.regionB }} · {{ result.period.start }} — {{ result.period.end }}</span>
          <h2>{{ result.label }}</h2><span class="verdict" :class="result.significant ? 'good' : 'caution'">{{ result.significant ? t.significant : t.notSignificant }}</span>
          <div class="rate-value">{{ formatRate(result.trend.slope_ols, result.rate_unit) }}</div><div class="rate-label">{{ t.rate }}</div>
          <p>{{ result.summary[locale] }}</p>
          <VChart class="comparison-chart" :option="index === 0 ? comparisonOptionA : comparisonOptionB" autoresize />
          <p class="chart-footnote">{{ result.trend.n_valid }} {{ t.observations }} · p (OLS) {{ formatPValue(result.trend.p_ols) }}</p>
        </article>
      </div>
      <p v-if="comparison" class="compare-caveat">{{ t.compareCaveat }}</p>
    </main>

    <main v-if="page === 'explore'" class="workspace">
      <aside class="control-panel">
        <div class="panel-head">
          <div><span class="eyebrow">{{ t.parameters }}</span><span class="dataset-pill">{{ activeVariable?.source }}</span></div>
          <button class="icon-button" :aria-label="t.guided" title="Guided investigation" @click="beginWizard">?</button>
        </div>
        <div class="panel-scroll">
          <section class="parameter-card">
            <span class="step-label">01 · {{ t.variable }}</span>
            <label class="field-label" for="variable-select">{{ t.variable }}</label>
            <select id="variable-select" v-model="selectedVariable">
              <option v-for="item in catalogVariables" :key="item.id" :value="item.id">
                {{ locale === 'fr' ? item.name_fr : item.name }}{{ item.status !== 'analysis_ready' ? ` · ${item.short_name ?? item.status}` : '' }}
              </option>
            </select>
            <h1>{{ activeVariable?.[locale === 'en' ? 'name' : 'name_fr'] ?? 'Surface temperature anomaly' }}</h1>
            <p>{{ activeVariable?.[locale === 'en' ? 'definition' : 'definition_fr'] }}</p>
            <p v-if="activeVariable?.status !== 'analysis_ready'" class="field-help">{{ activeVariable?.status === 'blocked_eula' ? t.accessBlocked : activeVariable?.status === 'acquiring' ? t.acquiring : activeVariable?.status === 'series_processed' ? t.seriesProcessed : t.sampleOnly }} — {{ activeVariable?.status_detail }}</p>
            <div class="metadata-row"><span>{{ activeVariable?.period }}</span></div>
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
            <button class="button primary full-button" :disabled="loading || !isAnalysisReady" @click="runAnalysis">{{ loading ? t.loading : t.apply }}</button>
          </section>

          <section v-if="analysis" class="result-card">
            <div class="result-heading"><span class="step-label">{{ t.summary }}</span><span class="verdict" :class="analysis.significant ? 'good' : 'caution'" :title="t.significanceHelp" :aria-label="t.significanceHelp">{{ analysis.significant ? '✓' : '◷' }} {{ statusText }}</span></div>
            <div class="rate-value">{{ formatRate(analysis.trend.slope_ols, analysis.rate_unit) }}</div>
            <div class="rate-label">{{ t.rate }} <span class="info" :title="t.m1">ⓘ</span></div>
            <div class="confidence-row"><span>{{ t.confidence }} <span class="info" :title="t.confidenceHelp" :aria-label="t.confidenceHelp">ⓘ</span></span><strong>{{ formatRate(analysis.trend.slope_ols_lo, analysis.rate_unit) }} – {{ formatRate(analysis.trend.slope_ols_hi, analysis.rate_unit) }}</strong></div>
            <div class="test-grid">
              <div :title="`${t.pValueHelp} ${t.m1}`"><span>{{ t.ols }} ⓘ</span><strong>p {{ formatPValue(analysis.trend.p_ols) }}</strong></div>
              <div :title="`${t.pValueHelp} ${t.m2}`"><span>{{ t.mk }} ⓘ</span><strong>p {{ formatPValue(analysis.trend.p_mk) }}</strong></div>
            </div>
            <p v-if="testConflict" class="period-note conflict-note">{{ t.testConflict }}</p>
            <p class="plain-summary">{{ analysis.summary[locale] }}</p>
            <p v-if="!analysis.significant" class="period-note">{{ t.longerPeriod }}</p>
          </section>
          <div v-if="error" class="error-message" role="alert">{{ error }} <button class="text-button" :aria-label="t.close" :title="t.close" @click="error = ''">×</button></div>
        </div>
        <footer class="panel-footer"><span class="source-dot"></span>{{ activeVariable?.source }} <a v-if="activeVariable?.doi" :href="`https://doi.org/${activeVariable.doi}`" target="_blank" rel="noreferrer">DOI ↗</a></footer>
      </aside>

      <section class="map-workspace" aria-label="Trend map and time series">
        <div class="map-heading">
          <div><span class="eyebrow">{{ t.mapTitle }}</span><p>{{ t.mapHelp }}</p></div>
          <label class="map-period"><span>{{ t.mapWindow }}</span><select v-model="mapWindow"><option v-for="window in activeVariable?.windows ?? ['full']" :key="window" :value="window">{{ window === 'full' ? t.full : window === '2010-fin' ? t.since2010 : t.since2015 }}</option></select></label>
        </div>
        <div ref="mapElement" class="map-canvas" :aria-label="t.mapTitle"></div>
        <div class="map-overlay-label"><span class="overlay-swatch"></span>{{ t.slopeLayer }} · {{ mapLayer?.slope_unit }} <span class="subtle-separator">|</span> {{ t.nonsignificantLayer }}</div>
        <div class="map-legend" aria-label="Diverging trend palette legend"><span>{{ mapLayer?.scale_min.toFixed(3) ?? '−' }}</span><div class="legend-gradient"></div><span>0</span><span class="legend-gradient reverse"></span><span>+{{ Math.abs(mapLayer?.scale_max ?? 0).toFixed(3) }}</span><small>{{ mapLayer?.slope_unit }}</small></div>
        <div v-if="mapLoading" class="map-loading">{{ t.loadingMap }}</div>
        <div class="map-attribution">Basemap: NASA GIBS Blue Marble. Trend overlay: {{ activeVariable?.source }}.</div>

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

    <main v-if="page === 'methods'" class="content-page">
      <div class="content-heading"><span class="eyebrow">SCIENTIFIC TRANSPARENCY</span><h1>{{ t.methods }}</h1><p>{{ t.methodsIntro }}</p></div>
      <div class="method-grid">
        <article><span class="method-index">01</span><h2>{{ t.ols }}</h2><p>{{ t.m1 }}</p><span class="method-formula">y = a + bt · rate unit follows variable · 95% CI</span></article>
        <article><span class="method-index">02</span><h2>{{ t.mk }} + Sen</h2><p>{{ t.m2 }}</p><span class="method-formula">Median of pairwise slopes</span></article>
        <article><span class="method-index">03</span><h2>{{ t.hr }} + FDR</h2><p>{{ t.m3 }}</p><span class="method-formula">BH false discovery rate · α = 0.10</span></article>
      </div>
      <article class="validation-card"><span class="eyebrow">{{ t.validation }}</span><p>{{ t.validation }}</p><a href="https://data.giss.nasa.gov/gistemp/data_v4.html" target="_blank" rel="noreferrer">NASA GISTEMP v4 data and methods ↗</a></article>
      <article class="validation-card"><h2>{{ t.limitations }}</h2><p>{{ activeVariable?.limitations }}</p><p>{{ t.disclaimer }}</p></article>
    </main>

    <main v-if="page === 'about'" class="content-page about-page">
      <span class="brand-mark large" aria-hidden="true">◎</span><h1>{{ t.aboutTitle }}</h1><p>{{ t.aboutText }}</p>
      <section class="validation-card"><h2>{{ t.notOfficial }}</h2><p>{{ locale === 'fr' ? 'L’application calcule des tendances descriptives sur les séries NASA prétraitées. Elle ne fournit ni prévision ni attribution causale.' : 'The application calculates descriptive trends from processed NASA records. It does not provide forecasts or causal attribution.' }}</p><p>{{ t.disclaimer }}</p></section>
      <section class="validation-card"><h2>{{ t.data }} · NASA</h2><ul class="credits-list"><li v-for="item in catalogVariables" :key="item.id"><span>{{ locale === 'fr' ? item.name_fr : item.name }} · {{ item.source }} <small>({{ statusLabel(item.status) }})</small></span><a v-if="item.doi" :href="`https://doi.org/${item.doi}`" target="_blank" rel="noreferrer">{{ item.doi }} ↗</a></li></ul><a href="https://data.giss.nasa.gov/gistemp/data_v4.html" target="_blank" rel="noreferrer">NASA GISTEMP v4 source ↗</a></section>
    </main>

    <div v-if="showExport" class="modal-backdrop" role="presentation" @click.self="showExport = false">
      <section class="dialog export-dialog" role="dialog" aria-modal="true" aria-labelledby="export-title">
        <div class="dialog-top"><div><span class="eyebrow">{{ t.exportTitle }}</span><h2 id="export-title">{{ locale === 'fr' ? (activeVariable?.name_fr ?? '') : (activeVariable?.name ?? '') }}</h2></div><button class="icon-button" :aria-label="t.close" @click="showExport = false">×</button></div>
        <p class="dialog-note">{{ analysis?.period.start }} — {{ analysis?.period.end }} · {{ selectedLabel }} · {{ activeVariable?.unit }}</p>
        <a class="export-option" :href="regionalCsvUrl"><span><strong>{{ t.exportCSV }}</strong><small>{{ locale === 'fr' ? 'Valeurs observées, cycle saisonnier et anomalies de la région choisie.' : 'Observed values, seasonal cycle, and anomalies for the selected region.' }}</small></span><b>CSV ↓</b></a>
        <a class="export-option" :href="slopePngUrl"><span><strong>{{ t.exportPNG }}</strong><small>{{ locale === 'fr' ? 'Carte de pente précalculée pour la variable et la fenêtre sélectionnées.' : 'Precomputed slope map for the selected variable and window.' }}</small></span><b>PNG ↓</b></a>
        <a class="export-option" :href="trendTifUrl"><span><strong>{{ t.exportTIF }}</strong><small>{{ t.exportNote }}</small></span><b>TIFF ↓</b></a>
      </section>
    </div>

    <div v-if="showWizard" class="modal-backdrop" role="presentation" @click.self="showWizard = false">
      <section class="dialog wizard-dialog" role="dialog" aria-modal="true" aria-labelledby="wizard-title">
        <div class="dialog-top"><span class="eyebrow">{{ t.guided }}</span><button class="icon-button" :aria-label="t.close" @click="showWizard = false">×</button></div>
        <div class="wizard-progress"><span v-for="step in 3" :key="step" :class="{ filled: step <= wizardStep }"></span></div>
        <span class="step-label">{{ locale === 'en' ? 'STEP' : 'ÉTAPE' }} {{ wizardStep }} / 3</span>
        <template v-if="wizardStep === 1"><h2 id="wizard-title">{{ t.theme }}</h2><div class="choice-grid"><button v-for="choice in [['climate', t.themeClimate], ['water', t.themeWater], ['vegetation', t.themePlants], ['air', t.themeAir]]" :key="choice[0]" :class="{ chosen: wizardTheme === choice[0] }" @click="wizardTheme = choice[0]">{{ choice[1] }}</button></div></template>
        <template v-else-if="wizardStep === 2"><h2 id="wizard-title">{{ t.where }}</h2><label class="field-label" for="wizard-place">{{ t.place }}</label><input id="wizard-place" v-model="wizardPlace" class="text-input" placeholder="e.g. Amazon" /><div class="quick-places"><button v-for="region in regions" :key="region.id" @click="wizardPlace = locale === 'fr' ? region.name_fr : region.name">{{ locale === 'fr' ? region.name_fr : region.name }}</button></div></template>
        <template v-else><h2 id="wizard-title">{{ t.variable }}</h2><div class="wizard-variable"><strong>{{ wizardVariable?.[locale === 'en' ? 'name' : 'name_fr'] }}</strong><p>{{ wizardVariable?.[locale === 'en' ? 'definition' : 'definition_fr'] }}</p><span>{{ wizardVariable?.source }}</span><p v-if="!wizardVariableReady" class="wizard-pending">{{ wizardVariableId === 'omi_no2' ? t.qualityPending : t.variablePending }}</p></div></template>
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
