<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { Analysis, Comparison, MapLayer, RegionInfo, VariableInfo } from './api'
import { api } from './api'
import { comparisonDirection, fittedLine, formatPValue, formatRate, stepMapZoom } from './trendUtils'
import { variablesForTheme, type WizardTheme } from './wizardThemes'
import { useMap } from './useMap'
import ExternalSources from './ExternalSources.vue'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

type Locale = 'en' | 'fr'
type WindowId = 'full' | '2010-fin' | '2015-fin'
type AppPage = 'home' | 'explore' | 'variables' | 'compare' | 'resources' | 'methods' | 'about'

const copy = {
  en: {
    home: 'Home', variablesPage: 'Variables', comparePage: 'Compare', resourcesPage: 'Data tools',
    homeTitle: 'Is the Earth changing where you live?',
    homeLead: 'Explore NASA Earth science data for a place you choose. Follow the time series, estimate a linear trend, and inspect its statistical evidence.',
    startInvestigation: 'Start investigating', browseVariables: 'Browse variables', watchVideo: 'Try a guided example',
    heroFacts: 'Monthly records · Regional analysis · Statistical tests',
    mapPreview: 'Global trend layer', mapPreviewPeriod: 'Processed GISTEMP v4 record', mapPreviewNote: 'Observed global slope layer · non-significant cells are stippled',
    zoomIn: 'Zoom in', zoomOut: 'Zoom out', recenterMap: 'Recenter map',
    howKicker: 'A REPEATABLE WORKFLOW', howTitle: 'How it works', howLead: 'From a question about a place to a result you can inspect.',
    howChoose: 'Choose a variable', howChooseText: 'Browse measured and modelled NASA products with their definitions, units, sources, and available periods.',
    howRegion: 'Choose a region', howRegionText: 'Select an example region or draw a custom area to calculate its area-weighted monthly series.',
    howAnalyze: 'Read the evidence', howAnalyzeText: 'Inspect the series, linear rate, confidence interval, and significance tests together.',
    videoKicker: 'DEMO VIDEO', videoTitle: 'See how an investigation works', videoText: 'The project walkthrough video will be added here.', guidedExamples: 'Explore guided examples',
    inventory: 'DATA AVAILABLE NOW', readyDatasets: 'variables ready for analysis',
    processingDatasets: 'in progress', variableSearch: 'Search verified variables', allStatuses: 'All statuses',
    readyStatus: 'Analysis ready', compareTitle: 'Compare two regions',
    loadingVariables: 'Loading analysis-ready variables…', noAvailableVariables: 'The API has not returned any analysis-ready variables.',
    compareIntro: 'Use the same available variable and full record for both regions. Results are calculated from their actual processed series.',
    compareSynthesis: 'Comparison summary', compareOpposite: 'Estimated trends point in opposite directions', compareSameUp: 'Both regions have positive estimated trends', compareSameDown: 'Both regions have negative estimated trends', compareFlat: 'The estimated trends include a near-zero rate', compareSynthesisText: (a: string, aRate: string, aSig: string, b: string, bRate: string, bSig: string) => `${a}: ${aRate} (${aSig}). ${b}: ${bRate} (${bSig}). This describes the selected records; it does not identify a cause.`,
    significantLabel: 'statistically significant', notSignificantLabel: 'not statistically significant',
    regionA: 'Region A', regionB: 'Region B', runCompare: 'Compare regions', rateA: 'Region A rate', rateB: 'Region B rate',
    compareCaveat: 'Differences describe the selected regional averages. They do not establish a cause.',
    exportTitle: 'Export real analysis products', exportCSV: 'Regional monthly series (CSV)',
    exportPNG: 'Precomputed trend map (PNG)', exportTIF: 'Trend grid (GeoTIFF)',
    exportNote: 'Exports use the selected processed dataset. Map files are available only when generated.',
    notOfficial: 'Independent project; not an official NASA product.',
    footerNote: 'Results describe statistical trends in the selected records; they do not establish causes.', footerExplore: 'Explore', footerScience: 'Science', footerProject: 'Project', footerSources: 'Data sources',
    explore: 'Explore', methods: 'Methods & validation', about: 'About', lang: 'Français', language: 'Language',
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
    senSlope: 'Sen slope · 95% interval', pettittTitle: 'Pettitt candidate change point', pettittSignificant: 'candidate shift (p < 0.05)', pettittNotSignificant: 'no statistically significant shift (p ≥ 0.05)',
    raw: 'Monthly values', deseasoned: 'Deseasonalized', trend: 'Linear trend',
    guided: 'Guided investigation', demo: 'Try a guided example', demoTitle: 'Guided examples',
    startDemo: 'Explore example', next: 'Next step', finish: 'Show result', close: 'Close',
    wizardPlaceNotFound: 'The selected example region is unavailable. Choose one of the listed regions.',
    demoDataUnavailable: 'The demo data could not be loaded. Please try again.', demoRegionUnavailable: 'The Amazon example region is missing from the region list.',
    theme: 'What interests you?', themeClimate: 'Climate', themeWater: 'Water',
    themePlants: 'Vegetation', themeAir: 'Atmosphere & air quality', where: 'Where should we look?',
    source: 'NASA GISS GISTEMP v4', unit: 'K / year', mapTitle: 'Global trend discovery map',
    mapHelp: 'Red cells show positive trends and blue shows negative trends. Dots mark cells that did not pass the map significance threshold. Click a cell to inspect its series.',
    mapLayers: 'Map layers', slopeLayerToggle: 'Trend slope', significanceLayerToggle: 'Non-significant cells', slopeOpacity: 'Slope opacity', opacityHelp: 'This slider affects the trend-color layer only; significance dots keep their own contrast.',
    negativeTrend: 'Blue · negative trend', nearZeroTrend: 'Near zero', positiveTrend: 'Red · positive trend', nonsignificantMeaning: 'Black dots · not significant after map FDR (q ≤ 0.10)', missingMeaning: 'Transparent · no valid data',
    noData: 'Processed GISTEMP is not available. Run `make preprocess` to generate it.',
    testConflict: 'The basic and autocorrelation-adjusted tests differ. Check the p-values and confidence interval before drawing a conclusion.',
    disclaimer: 'A significant trend describes statistical evidence of change; it does not identify its cause.',
    aboutTitle: 'Earth Trend Detective', aboutText: 'An educational tool for exploring NASA Earth observations by place and time.',
    data: 'Data & credits', limitations: 'Limitations', periodShort: 'period', coordinates: 'Selected grid cell',
    dataScope: 'The catalogue below lists the NASA products and analysis periods configured in the app, with their current processing status. Supporting map imagery and the independent validation series are listed separately.', supportingData: 'Supporting data and map imagery', basemapRole: 'Geographic background only; not used to calculate trends.', validationRole: 'Independent reference used to validate the GISTEMP gridded global mean; not an input to regional trend analysis.',
    choose: 'Select',
    methodsIntro: 'Regional statistics are calculated from deseasonalized monthly series. The discovery map uses per-cell trend estimates with a multiple-testing correction.',
    m1: 'Ordinary least squares (OLS) fits a straight line to deseasonalized monthly values. Its two-sided t test and 95% confidence interval assume independent, normally distributed residuals; serial correlation can make this test too optimistic.',
    m2: 'Mann–Kendall tests for a monotonic direction without assuming normally distributed values. Sen’s slope is the median of pairwise slopes and has a 95% confidence interval. These rank-based results complement, rather than replace, the OLS rate.',
    m3: 'The regional Hamed–Rao modified Mann–Kendall p-value adjusts variance for serial dependence (up to three lags in this implementation). The map applies Benjamini–Hochberg false discovery rate correction at α = 0.10 across valid cells. Hamed–Rao can be unavailable for some series.',
    seasonalityMethod: 'For each position in the repeating 12-month cycle, the selected series’ mean is calculated across the selected period and subtracted from matching positions. Trend statistics use these deseasonalized values. This is a simple monthly-climatology adjustment, not a full STL decomposition.',
    breakMethod: 'Pettitt’s rank test reports the strongest candidate split in a regional or point series and an approximate p-value. A candidate shift is not a cause, and a linear trend can influence this one-break test; interpret it alongside the trend statistics.',
    validation: 'Validation against NASA’s published global monthly series for 1980-01 through 2026-09 (561 overlapping months): bias 0.00267 K, RMSE 0.05006 K, maximum absolute difference 0.18366 K. The gridded and NASA published slopes were 0.0210564 and 0.0210556 K/year, respectively (difference 0.0000008 K/year). The global means use different averaging methods.',
    references: 'Method references',
    mapWindow: 'Map window',
    blankMap: 'Trend layer unavailable', point: 'Point', region: 'Region',
    dataFrequency: 'Monthly · 2° grid', fieldHelp: 'Choose an example area or drag over the map.',
    slopeLayer: 'OLS slope', nonsignificantLayer: 'dots = not significant', observations: 'months',
  },
  fr: {
    home: 'Accueil', variablesPage: 'Variables', comparePage: 'Comparer', resourcesPage: 'Ressources',
    homeTitle: 'La Terre change-t-elle là où vous vivez ?',
    homeLead: 'Explorez les données NASA des sciences de la Terre pour un lieu de votre choix. Suivez la série temporelle, estimez une tendance linéaire et examinez les preuves statistiques.',
    startInvestigation: 'Commencer l’enquête', browseVariables: 'Parcourir les variables', watchVideo: 'Essayer un exemple guidé',
    heroFacts: 'Séries mensuelles · Analyse régionale · Tests statistiques',
    mapPreview: 'Couche mondiale de tendance', mapPreviewPeriod: 'Série GISTEMP v4 traitée', mapPreviewNote: 'Pente globale observée · les mailles non significatives sont pointillées',
    zoomIn: 'Agrandir la carte', zoomOut: 'Réduire la carte', recenterMap: 'Recentrer la carte',
    howKicker: 'UN PARCOURS REPRODUCTIBLE', howTitle: 'Comment ça marche', howLead: 'D’une question sur un lieu à un résultat que vous pouvez examiner.',
    howChoose: 'Choisir une variable', howChooseText: 'Parcourez les produits NASA mesurés ou modélisés, avec leurs définitions, unités, sources et périodes disponibles.',
    howRegion: 'Choisir une région', howRegionText: 'Sélectionnez une région d’exemple ou dessinez une zone pour calculer sa série mensuelle pondérée par la surface.',
    howAnalyze: 'Examiner les résultats', howAnalyzeText: 'Consultez ensemble la série, le taux linéaire, l’intervalle de confiance et les tests de significativité.',
    videoKicker: 'VIDÉO DÉMO', videoTitle: 'Voir une enquête en action', videoText: 'La vidéo de présentation du projet sera ajoutée ici.', guidedExamples: 'Explorer les exemples guidés',
    inventory: 'DONNÉES DISPONIBLES', readyDatasets: 'variables analysables',
    processingDatasets: 'en cours', variableSearch: 'Rechercher une variable vérifiée', allStatuses: 'Tous les états',
    readyStatus: 'Analyse disponible', compareTitle: 'Comparer deux régions',
    loadingVariables: 'Chargement des variables analysables…', noAvailableVariables: 'L’API n’a renvoyé aucune variable analysable.',
    compareIntro: 'Une même variable et toute la période disponible sont utilisées dans les deux régions. Les résultats sont calculés à partir des séries traitées.',
    compareSynthesis: 'Synthèse de la comparaison', compareOpposite: 'Les tendances estimées sont de sens opposé', compareSameUp: 'Les tendances estimées sont positives dans les deux régions', compareSameDown: 'Les tendances estimées sont négatives dans les deux régions', compareFlat: 'Les tendances estimées comprennent un taux proche de zéro', compareSynthesisText: (a: string, aRate: string, aSig: string, b: string, bRate: string, bSig: string) => `${a} : ${aRate} (${aSig}). ${b} : ${bRate} (${bSig}). Cela décrit les séries sélectionnées, sans identifier de cause.`,
    significantLabel: 'statistiquement significative', notSignificantLabel: 'pas statistiquement significative',
    regionA: 'Région A', regionB: 'Région B', runCompare: 'Comparer les régions', rateA: 'Taux région A', rateB: 'Taux région B',
    compareCaveat: 'Les différences décrivent les moyennes régionales choisies ; elles ne démontrent pas une cause.',
    exportTitle: 'Exporter les résultats calculés', exportCSV: 'Série mensuelle régionale (CSV)',
    exportPNG: 'Carte de tendance précalculée (PNG)', exportTIF: 'Grille de tendance (GeoTIFF)',
    exportNote: 'Les exports utilisent les données traitées sélectionnées. Les cartes sont disponibles uniquement si elles ont été générées.',
    notOfficial: 'Projet indépendant ; ce n’est pas un produit officiel de la NASA.',
    footerNote: 'Les résultats décrivent des tendances statistiques dans les données choisies ; ils n’en établissent pas les causes.', footerExplore: 'Explorer', footerScience: 'Méthodes', footerProject: 'Projet', footerSources: 'Sources des données',
    explore: 'Explorer', methods: 'Méthodes et validation', about: 'À propos', lang: 'English', language: 'Langue',
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
    senSlope: 'Pente de Sen · intervalle à 95 %', pettittTitle: 'Point de rupture candidat (Pettitt)', pettittSignificant: 'rupture candidate (p < 0,05)', pettittNotSignificant: 'pas de rupture statistiquement significative (p ≥ 0,05)',
    raw: 'Valeurs mensuelles', deseasoned: 'Désaisonnalisée', trend: 'Tendance linéaire',
    guided: 'Parcours guidé', demo: 'Voir un exemple guidé', demoTitle: 'Exemples guidés',
    startDemo: 'Explorer cet exemple', next: 'Étape suivante', finish: 'Voir le résultat', close: 'Fermer',
    wizardPlaceNotFound: 'La région choisie est indisponible. Choisissez une région dans la liste.',
    demoDataUnavailable: 'Les données nécessaires à la démo n’ont pas pu être chargées. Réessayez.', demoRegionUnavailable: 'La région d’exemple de l’Amazonie est absente de la liste des régions.',
    theme: 'Quel thème vous intéresse ?', themeClimate: 'Climat', themeWater: 'Eau',
    themePlants: 'Végétation', themeAir: 'Atmosphère et qualité de l’air', where: 'Où regarder ?',
    source: 'NASA GISS GISTEMP v4', unit: 'K / an', mapTitle: 'Carte mondiale des tendances',
    mapHelp: 'Le rouge indique une tendance positive et le bleu une tendance négative. Les points marquent les mailles qui ne passent pas le seuil statistique. Cliquez sur une maille pour voir sa série.',
    mapLayers: 'Couches de la carte', slopeLayerToggle: 'Pente de tendance', significanceLayerToggle: 'Mailles non significatives', slopeOpacity: 'Opacité de la pente', opacityHelp: 'Ce curseur agit uniquement sur la couleur de la tendance ; les points de significativité gardent leur contraste.',
    negativeTrend: 'Bleu · tendance négative', nearZeroTrend: 'Proche de zéro', positiveTrend: 'Rouge · tendance positive', nonsignificantMeaning: 'Points noirs · non significatif après FDR sur la carte (q ≤ 0,10)', missingMeaning: 'Transparent · aucune donnée valide',
    noData: 'GISTEMP prétraité est indisponible. Lancez `make preprocess` pour le générer.',
    testConflict: 'Les tests simple et corrigé de l’autocorrélation diffèrent. Comparez les valeurs p et l’intervalle avant toute conclusion.',
    disclaimer: 'Une tendance significative indique une preuve statistique de changement, pas sa cause.',
    aboutTitle: 'Détective des tendances terrestres', aboutText: 'Un outil pédagogique pour explorer les observations NASA selon le lieu et la période.',
    data: 'Données et crédits', limitations: 'Limites', periodShort: 'période', coordinates: 'Maille sélectionnée',
    dataScope: 'Le catalogue ci-dessous répertorie les produits NASA et périodes configurés dans l’application, avec leur état de traitement actuel. Le fond cartographique et la série de validation indépendante sont indiqués séparément.', supportingData: 'Données et fond cartographique complémentaires', basemapRole: 'Fond géographique uniquement ; il ne sert pas au calcul des tendances.', validationRole: 'Référence indépendante pour valider la moyenne globale maillée GISTEMP ; elle n’entre pas dans l’analyse des tendances régionales.',
    choose: 'Choisir',
    methodsIntro: 'Les statistiques régionales sont calculées à partir des séries mensuelles désaisonnalisées. La carte de repérage estime les tendances par maille et corrige les tests multiples.',
    m1: 'Les moindres carrés ordinaires (MCO) ajustent une droite aux valeurs mensuelles désaisonnalisées. Le test t bilatéral et l’intervalle de confiance à 95 % supposent des résidus indépendants et normalement distribués ; l’autocorrélation peut rendre ce test trop optimiste.',
    m2: 'Mann–Kendall teste une évolution monotone sans supposer une distribution normale. La pente de Sen est la médiane des pentes entre paires et son intervalle de confiance est à 95 %. Ces résultats fondés sur les rangs complètent le taux MCO, sans le remplacer.',
    m3: 'La valeur p régionale Hamed–Rao modifie la variance du test Mann–Kendall pour tenir compte de la dépendance temporelle (jusqu’à trois retards ici). La carte applique la correction du taux de fausses découvertes de Benjamini–Hochberg, α = 0,10, aux mailles valides. Hamed–Rao peut être indisponible pour certaines séries.',
    seasonalityMethod: 'Pour chaque position du cycle de 12 mois, la moyenne de la série sur la période choisie est calculée puis soustraite aux positions correspondantes. Les statistiques de tendance utilisent ces valeurs désaisonnalisées. C’est une correction simple par climatologie mensuelle, pas une décomposition STL complète.',
    breakMethod: 'Le test de rang de Pettitt indique la séparation candidate la plus marquée d’une série régionale ou ponctuelle et une valeur p approchée. Cette rupture candidate n’en établit pas la cause ; une tendance linéaire peut aussi influencer ce test à une rupture. Il faut le lire avec les statistiques de tendance.',
    validation: 'Validation avec la série mensuelle globale publiée par NASA, de 1980-01 à 2026-09 (561 mois communs) : biais 0,00267 K, RMSE 0,05006 K, écart absolu maximal 0,18366 K. Les pentes de la grille et de la série NASA publiée sont respectivement de 0,0210564 et 0,0210556 K/an (écart de 0,0000008 K/an). Les moyennes globales utilisent des méthodes de calcul différentes.',
    references: 'Références des méthodes',
    mapWindow: 'Période de la carte',
    blankMap: 'Carte de tendance indisponible', point: 'Point', region: 'Région',
    dataFrequency: 'Mensuel · grille de 2°', fieldHelp: 'Choisissez une zone ou tracez-la sur la carte.',
    slopeLayer: 'Pente MCO', nonsignificantLayer: 'points = non significatif', observations: 'mois',
  },
} as const

const locale = ref<Locale>('fr')
const t = computed(() => copy[locale.value])
const wizardThemeOptions = computed(() => [
  { id: 'climate' as const, label: t.value.themeClimate },
  { id: 'water' as const, label: t.value.themeWater },
  { id: 'vegetation' as const, label: t.value.themePlants },
  { id: 'air' as const, label: t.value.themeAir },
])
const page = ref<AppPage>('home')
const mapElement = ref<HTMLElement | null>(null)
const mapLayer = ref<MapLayer | null>(null)
const showSlopeLayer = ref(true)
const showSignificanceLayer = ref(true)
const slopeOpacity = ref(80)
const showMapLayers = ref(false)
const landingMapLayer = ref<MapLayer | null>(null)
const landingMapZoom = ref(1)
const mapWindow = ref<WindowId>('full')
const variables = ref<VariableInfo[]>([])
const catalogVariables = ref<VariableInfo[]>([])
// /api/variables already filters to analysis-ready records; its response schema
// intentionally omits catalog-only fields such as `status`.
const readyVariables = computed(() => variables.value.length
  ? variables.value
  : catalogVariables.value.filter((item) => item.status === 'analysis_ready'))
const gistempCatalogItem = computed(() => catalogVariables.value.find((item) => item.id === 'gistemp_tas_anom'))
const landingSlopeUrl = computed(() => api.exportUrl({
  variable: 'gistemp_tas_anom', format: 'png', window: 'full', layer: 'slope',
}))
const landingSignificanceUrl = computed(() => api.exportUrl({
  variable: 'gistemp_tas_anom', format: 'png', window: 'full', layer: 'nonsignificant',
}))
function zoomLandingMap(direction: -1 | 1) {
  landingMapZoom.value = stepMapZoom(landingMapZoom.value, direction)
}
const inventoryLoading = ref(true)
const catalogSearch = ref('')
const catalogStatus = ref('all')
const selectedVariable = ref('gistemp_tas_anom')
const wizardTheme = ref<WizardTheme>('climate')
const wizardVariableId = ref('gistemp_tas_anom')
const activeVariable = computed(() => catalogVariables.value.find((item) => item.id === selectedVariable.value)
  ?? readyVariables.value.find((item) => item.id === selectedVariable.value)
  ?? readyVariables.value[0])
const wizardVariables = computed(() => variablesForTheme(wizardTheme.value)
  .map((id) => catalogVariables.value.find((item) => item.id === id))
  .filter((item): item is VariableInfo => Boolean(item)))
const wizardVariable = computed(() => wizardVariables.value.find((item) => item.id === wizardVariableId.value))
const wizardVariableReady = computed(() => readyVariables.value.some((item) => item.id === wizardVariableId.value))
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
const wizardRegionId = ref('amazon')
const wizardRegion = computed(() => regions.value.find((item) => item.id === wizardRegionId.value))
const wizardPlace = computed(() => wizardRegion.value
  ? locale.value === 'fr' ? wizardRegion.value.name_fr : wizardRegion.value.name
  : '')
const showDemos = ref(false)
const demoStep = ref(0)
const activeDemo = ref('')
const demoError = ref('')
const chartMode = ref<'anomaly' | 'raw'>('anomaly')

const comparisonOptionA = computed(() => comparison.value ? comparisonChartOption(comparison.value.a) : {})
const comparisonOptionB = computed(() => comparison.value ? comparisonChartOption(comparison.value.b) : {})
const comparisonSynthesis = computed(() => {
  if (!comparison.value) return null
  const { a, b } = comparison.value
  const slopeA = a.trend.slope_ols
  const slopeB = b.trend.slope_ols
  if (slopeA === null || slopeB === null || !Number.isFinite(slopeA) || !Number.isFinite(slopeB)) {
    return { title: t.value.insufficient, text: t.value.compareCaveat }
  }
  const direction = comparisonDirection(slopeA, slopeB)
  const title = direction === 'opposite'
    ? t.value.compareOpposite
    : direction === 'same_up'
      ? t.value.compareSameUp
      : direction === 'same_down'
        ? t.value.compareSameDown
        : t.value.compareFlat
  const significance = (value: boolean) => value ? t.value.significantLabel : t.value.notSignificantLabel
  return {
    title,
    text: t.value.compareSynthesisText(
      a.label, formatRate(slopeA, a.rate_unit), significance(a.significant),
      b.label, formatRate(slopeB, b.rate_unit), significance(b.significant),
    ),
  }
})
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
  clearSelectedRegion()
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

function chooseWizardTheme(theme: WizardTheme) {
  wizardTheme.value = theme
  const themeIds = variablesForTheme(theme)
  wizardVariableId.value = themeIds.find((id) => readyVariables.value.some((item) => item.id === id))
    ?? themeIds[0]
    ?? ''
}

function isWizardVariableReady(id: string) {
  return readyVariables.value.some((item) => item.id === id)
}

async function wizardNext() {
  if (wizardStep.value < 3) {
    wizardStep.value++
    return
  }
  if (!wizardVariable.value || !wizardVariableReady.value) return
  const match = wizardRegion.value
  if (!match) {
    showWizard.value = false
    page.value = 'explore'
    selectedVariable.value = wizardVariableId.value
    error.value = t.value.wizardPlaceNotFound
    return
  }
  showWizard.value = false
  page.value = 'explore'
  selectedVariable.value = wizardVariableId.value
  chooseRegion(match.id)
}

async function startDemo(id: string) {
  demoError.value = ''
  try {
    const [loadedRegions, loadedVariables] = await Promise.all([
      regions.value.length ? Promise.resolve(regions.value) : api.regions(),
      readyVariables.value.some((item) => item.id === 'gistemp_tas_anom')
        ? Promise.resolve(readyVariables.value)
        : api.variables(),
    ])
    if (!regions.value.length) regions.value = loadedRegions
    if (!readyVariables.value.some((item) => item.id === 'gistemp_tas_anom')) variables.value = loadedVariables
    if (!readyVariables.value.some((item) => item.id === 'gistemp_tas_anom')) {
      demoError.value = t.value.demoDataUnavailable
      return
    }
    const region = id === 'arctic' ? null : regions.value.find((item) => item.id === id)
    if (id !== 'arctic' && !region) {
      demoError.value = t.value.demoRegionUnavailable
      return
    }

    page.value = 'explore'
    selectedVariable.value = 'gistemp_tas_anom'
    activeDemo.value = id
    demoStep.value = 1
    period.value = 'full'
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
    showDemos.value = false
    await nextTick()
    resizeMap()
    await Promise.all([loadMap(), runAnalysis()])
    demoStep.value = 1
  } catch {
    demoError.value = t.value.demoDataUnavailable
  }
}

function stepDemo() {
  if (demoStep.value >= 3) {
    demoStep.value = 0
    activeDemo.value = ''
  } else {
    demoStep.value++
  }
}

function openDemoPicker() {
  demoError.value = ''
  showDemos.value = true
}

const { drawing, startDrawing, cancelDrawing, clearSelectedRegion, resizeMap } = useMap(
  mapElement, mapLayer, selectedBounds, showSlopeLayer, showSignificanceLayer, slopeOpacity,
  inspectPoint, chooseDrawnRegion,
)

watch([page, isAnalysisReady], async ([currentPage, ready]) => {
  if (currentPage !== 'explore' || !ready) return
  await nextTick()
  requestAnimationFrame(() => resizeMap())
  void loadMap()
}, { flush: 'post' })

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
  void api.map('gistemp_tas_anom', 'full').then((layer) => { landingMapLayer.value = layer }).catch(() => {})
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
        <button :class="{ active: page === 'resources' }" @click="page = 'resources'">{{ t.resourcesPage }}</button>
        <button :class="{ active: page === 'methods' }" @click="page = 'methods'">{{ t.methods }}</button>
        <button :class="{ active: page === 'about' }" @click="page = 'about'">{{ t.about }}</button>
      </nav>
      <div class="top-actions">
        <div class="language-switch" role="group" :aria-label="t.language">
          <svg class="language-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/></svg>
          <button :class="{ selected: locale === 'en' }" :aria-pressed="locale === 'en'" @click="locale = 'en'">EN</button>
          <span aria-hidden="true">|</span>
          <button :class="{ selected: locale === 'fr' }" :aria-pressed="locale === 'fr'" @click="locale = 'fr'">FR</button>
        </div>
        <button v-if="page === 'explore' && isAnalysisReady" class="button secondary compact" @click="showExport = true">↓ <span>Export</span></button>
        <button class="button secondary compact" @click="openDemoPicker">▶ <span>{{ t.demo }}</span></button>
      </div>
    </header>

    <main v-if="page === 'home'" class="home-page">
      <section class="landing-hero">
        <span class="landing-kicker"><span class="status-dot"></span>{{ t.heroFacts }}</span>
        <h1>{{ t.homeTitle }}</h1>
        <p>{{ t.homeLead }}</p>
        <div class="landing-actions">
          <button class="button primary landing-primary" @click="page = 'explore'; beginWizard()">{{ t.startInvestigation }} <span aria-hidden="true">→</span></button>
          <button class="button secondary landing-secondary" @click="openDemoPicker"><span aria-hidden="true">▷</span> {{ t.watchVideo }}</button>
        </div>
      </section>

      <section class="landing-map-card" aria-labelledby="landing-map-title">
        <div class="landing-map-toolbar">
          <div><span class="eyebrow">{{ t.mapPreview }}</span><h2 id="landing-map-title">{{ gistempCatalogItem?.source ?? 'NASA GISS GISTEMP v4' }}</h2></div>
          <span class="map-period-chip">{{ gistempCatalogItem?.period ?? t.mapPreviewPeriod }}</span>
        </div>
        <div class="landing-world-map" role="group" :aria-label="`${t.mapPreview} — ${gistempCatalogItem?.source ?? 'NASA GISS GISTEMP v4'}`">
          <div class="landing-map-visual" :style="{ transform: `scale(${landingMapZoom})` }" aria-hidden="true">
            <img class="landing-slope-image" :src="landingSlopeUrl" alt="" />
            <img class="landing-significance-image" :src="landingSignificanceUrl" alt="" />
          </div>
          <div class="landing-map-controls" role="group" :aria-label="t.mapPreview">
            <button type="button" :aria-label="t.zoomIn" :title="t.zoomIn" :disabled="landingMapZoom >= 3" @click="zoomLandingMap(1)">+</button>
            <button type="button" :aria-label="t.zoomOut" :title="t.zoomOut" :disabled="landingMapZoom <= 1" @click="zoomLandingMap(-1)">−</button>
            <button type="button" class="recenter-map" :aria-label="t.recenterMap" :title="t.recenterMap" :disabled="landingMapZoom === 1" @click="landingMapZoom = 1">⌖</button>
          </div>
          <span v-if="!landingMapLayer" class="map-preview-loading">{{ t.loadingMap }}</span>
        </div>
        <div class="landing-map-legend">
          <span>{{ landingMapLayer?.scale_min.toFixed(3) ?? '−' }}</span>
          <div class="legend-gradient"></div><span>0</span><div class="legend-gradient reverse"></div>
          <span>+{{ Math.abs(landingMapLayer?.scale_max ?? 0).toFixed(3) }}</span><small>{{ landingMapLayer?.slope_unit ?? 'K/year' }}</small>
          <span class="landing-map-note">{{ t.mapPreviewNote }}</span>
        </div>
      </section>

      <section class="landing-section how-section">
        <div class="landing-section-heading"><span class="eyebrow">{{ t.howKicker }}</span><h2>{{ t.howTitle }}</h2><p>{{ t.howLead }}</p></div>
        <div class="landing-steps">
          <article><div class="landing-step-top"><span class="landing-step-icon" aria-hidden="true">◈</span><span class="method-index">01</span></div><h3>{{ t.howChoose }}</h3><p>{{ t.howChooseText }}</p></article>
          <article><div class="landing-step-top"><span class="landing-step-icon" aria-hidden="true">⌖</span><span class="method-index">02</span></div><h3>{{ t.howRegion }}</h3><p>{{ t.howRegionText }}</p></article>
          <article><div class="landing-step-top"><span class="landing-step-icon" aria-hidden="true">↗</span><span class="method-index">03</span></div><h3>{{ t.howAnalyze }}</h3><p>{{ t.howAnalyzeText }}</p></article>
        </div>
      </section>

      <section class="landing-section video-section">
        <div class="landing-section-heading"><span class="eyebrow">{{ t.videoKicker }}</span><h2>{{ t.videoTitle }}</h2><p>{{ t.videoText }}</p></div>
        <div class="video-placeholder">
          <div class="video-placeholder-content"><span class="video-play" aria-hidden="true">▷</span><strong>{{ t.videoKicker }}</strong><button class="text-button" @click="openDemoPicker">{{ t.guidedExamples }} →</button></div>
        </div>
      </section>

      <section class="landing-section ready-section">
        <div class="landing-inventory-heading"><div><span class="eyebrow">{{ t.inventory }}</span><h2>{{ locale === 'fr' ? 'Variables vérifiées et prêtes' : 'Verified variables ready to explore' }}</h2></div><div class="landing-inventory-actions"><div class="inventory-count"><strong>{{ readyVariables.length }}</strong><span>{{ t.readyDatasets }}</span></div><button class="text-button" @click="page = 'variables'">{{ t.browseVariables }} →</button></div></div>
        <div class="ready-chips"><button v-for="item in readyVariables" :key="item.id" @click="openVariable(item.id)">{{ locale === 'fr' ? item.name_fr : item.name }} <span>· {{ item.unit }}</span></button></div>
      </section>

      <footer class="landing-footer">
        <div class="landing-footer-top"><a class="landing-footer-brand" href="#home" @click.prevent="page = 'home'"><span class="brand-mark" aria-hidden="true">◎</span><span>Earth Trend Detective</span></a><p>{{ t.notOfficial }} {{ t.footerNote }}</p></div>
        <div class="landing-footer-links"><button @click="page = 'variables'">{{ t.footerExplore }} · {{ t.variablesPage }}</button><button @click="page = 'methods'">{{ t.footerScience }} · {{ t.methods }}</button><button @click="page = 'about'">{{ t.footerProject }} · {{ t.about }}</button></div>
        <div class="landing-footer-bottom"><span>{{ t.footerSources }} · NASA GISS GISTEMP v4 and products listed in the catalogue</span><span>© 2026 Earth Trend Detective</span></div>
      </footer>
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
      <section v-if="comparisonSynthesis" class="comparison-synthesis" aria-live="polite">
        <div><span class="eyebrow">{{ t.compareSynthesis }}</span><h2>{{ comparisonSynthesis.title }}</h2><p>{{ comparisonSynthesis.text }}</p></div>
        <div v-if="comparison" class="synthesis-directions" aria-hidden="true">
          <span class="direction-icon" :class="comparison.a.trend.slope_ols === null ? 'unknown' : comparison.a.trend.slope_ols >= 0 ? 'up' : 'down'">
            <svg v-if="comparison.a.trend.slope_ols !== null && comparison.a.trend.slope_ols >= 0" viewBox="0 0 24 24"><path d="m3 17 6-6 4 4 8-8M15 7h6v6"/></svg>
            <svg v-else-if="comparison.a.trend.slope_ols !== null" viewBox="0 0 24 24"><path d="m3 7 6 6 4-4 8 8m-6 0h6v-6"/></svg>
            <span v-else>?</span>
          </span>
          <svg class="direction-compare" aria-hidden="true" viewBox="0 0 24 24"><path d="M4 8h15m-4-4 4 4-4 4M20 16H5m4 4-4-4 4-4"/></svg>
          <span class="direction-icon" :class="comparison.b.trend.slope_ols === null ? 'unknown' : comparison.b.trend.slope_ols >= 0 ? 'up' : 'down'">
            <svg v-if="comparison.b.trend.slope_ols !== null && comparison.b.trend.slope_ols >= 0" viewBox="0 0 24 24"><path d="m3 17 6-6 4 4 8-8M15 7h6v6"/></svg>
            <svg v-else-if="comparison.b.trend.slope_ols !== null" viewBox="0 0 24 24"><path d="m3 7 6 6 4-4 8 8m-6 0h6v-6"/></svg>
            <span v-else>?</span>
          </span>
        </div>
      </section>
      <p v-if="comparison" class="compare-caveat">{{ t.compareCaveat }}</p>
    </main>

    <ExternalSources v-else-if="page === 'resources'" :locale="locale" :regions="regions" />

    <main v-if="page === 'explore'" class="workspace">
      <aside class="control-panel">
        <div class="panel-head">
          <div><span class="eyebrow">{{ t.parameters }}</span><span class="dataset-pill">{{ activeVariable?.source }}</span></div>
          <button class="icon-button guided-help-button" :aria-label="t.guided" :title="t.guided" @click="beginWizard">?</button>
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
            <div class="confidence-row sen-row" :title="t.m2"><span>{{ t.senSlope }} ⓘ</span><strong>{{ formatRate(analysis.trend.slope, analysis.rate_unit) }} · {{ formatRate(analysis.trend.slope_lo, analysis.rate_unit) }} – {{ formatRate(analysis.trend.slope_hi, analysis.rate_unit) }}</strong></div>
            <div class="test-grid">
              <div :title="`${t.pValueHelp} ${t.m1}`"><span>{{ t.ols }} ⓘ</span><strong>p {{ formatPValue(analysis.trend.p_ols) }}</strong></div>
              <div :title="`${t.pValueHelp} ${t.m2}`"><span>{{ t.mk }} ⓘ</span><strong>p {{ formatPValue(analysis.trend.p_mk) }}</strong></div>
              <div :title="`${t.pValueHelp} ${t.m3}`"><span>{{ t.hr }} ⓘ</span><strong>p {{ formatPValue(analysis.trend.p_value) }}</strong></div>
            </div>
            <p v-if="testConflict" class="period-note conflict-note">{{ t.testConflict }}</p>
            <div v-if="analysis.break" class="break-result" :title="t.breakMethod"><span>{{ t.pettittTitle }} · {{ analysis.break.date }}</span><strong>p {{ formatPValue(analysis.break.p) }} · {{ analysis.break.significant ? t.pettittSignificant : t.pettittNotSignificant }}</strong></div>
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
        <div class="map-layer-control">
          <button class="map-layer-trigger" type="button" :aria-expanded="showMapLayers" @click="showMapLayers = !showMapLayers">▤ {{ t.mapLayers }} <span>{{ showMapLayers ? '−' : '+' }}</span></button>
          <section v-if="showMapLayers" class="map-layer-panel" :aria-label="t.mapLayers">
            <label class="map-layer-toggle"><input v-model="showSlopeLayer" type="checkbox" />{{ t.slopeLayerToggle }}</label>
            <div class="map-opacity-heading"><label for="slope-opacity">{{ t.slopeOpacity }}</label><output for="slope-opacity">{{ slopeOpacity }}%</output></div>
            <input id="slope-opacity" v-model.number="slopeOpacity" class="map-opacity-slider" type="range" min="0" max="100" step="5" :disabled="!showSlopeLayer" :aria-label="t.slopeOpacity" />
            <p class="map-opacity-help">{{ t.opacityHelp }}</p>
            <label class="map-layer-toggle"><input v-model="showSignificanceLayer" type="checkbox" />{{ t.significanceLayerToggle }}</label>
            <div v-if="showSlopeLayer" class="map-layer-key">
              <span class="map-layer-gradient" aria-hidden="true"></span>
              <div class="map-layer-gradient-labels"><span>{{ t.negativeTrend }}</span><span>{{ t.nearZeroTrend }}</span><span>{{ t.positiveTrend }}</span></div>
              <small v-if="mapLayer">{{ mapLayer.scale_min.toFixed(3) }} — 0 — +{{ Math.abs(mapLayer.scale_max).toFixed(3) }} {{ mapLayer.slope_unit }}</small>
            </div>
            <div v-if="showSignificanceLayer" class="map-layer-note"><span class="map-dot-swatch" aria-hidden="true"></span>{{ t.nonsignificantMeaning }}</div>
            <div class="map-layer-note"><span class="map-transparent-swatch" aria-hidden="true"></span>{{ t.missingMeaning }}</div>
          </section>
        </div>
        <div ref="mapElement" class="map-canvas" :aria-label="t.mapTitle"></div>
        <div v-if="showSlopeLayer || showSignificanceLayer" class="map-overlay-label"><span v-if="showSlopeLayer" class="overlay-swatch"></span><span v-if="showSlopeLayer">{{ t.slopeLayer }} · {{ mapLayer?.slope_unit }}</span><span v-if="showSlopeLayer && showSignificanceLayer" class="subtle-separator">|</span><span v-if="showSignificanceLayer">{{ t.nonsignificantLayer }}</span></div>
        <div v-if="mapLayer && showSlopeLayer" class="map-legend" aria-label="Diverging trend palette legend"><span>{{ mapLayer.scale_min.toFixed(3) }}</span><div class="legend-gradient"></div><span>0</span><div class="legend-gradient reverse"></div><span>+{{ Math.abs(mapLayer.scale_max).toFixed(3) }}</span><small>{{ mapLayer.slope_unit }}</small></div>
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
      <div class="method-detail-grid">
        <article class="validation-card"><h2>{{ t.deseasoned }}</h2><p>{{ t.seasonalityMethod }}</p></article>
        <article class="validation-card"><h2>{{ t.pettittTitle }}</h2><p>{{ t.breakMethod }}</p></article>
      </div>
      <article class="validation-card"><span class="eyebrow">{{ t.validation }}</span><p>{{ t.validation }}</p><a href="https://data.giss.nasa.gov/gistemp/data_v4.html" target="_blank" rel="noreferrer">NASA GISTEMP v4 data and methods ↗</a></article>
      <article class="validation-card method-references"><h2>{{ t.references }}</h2><ul>
        <li><a href="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html" target="_blank" rel="noreferrer">SciPy · linear regression and t test</a></li>
        <li><a href="https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html" target="_blank" rel="noreferrer">SciPy · Theil–Sen slope</a></li>
        <li><a href="https://github.com/mmhs013/pyMannKendall" target="_blank" rel="noreferrer">pyMannKendall · Mann–Kendall and Hamed–Rao</a></li>
        <li><a href="https://doi.org/10.1016/S0022-1694(97)00125-X" target="_blank" rel="noreferrer">Hamed &amp; Rao (1998) · modified Mann–Kendall test</a></li>
        <li><a href="https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html" target="_blank" rel="noreferrer">Statsmodels · multiple-testing correction</a></li>
        <li><a href="https://github.com/mmhs013/pyHomogeneity" target="_blank" rel="noreferrer">pyHomogeneity · Pettitt test reference implementation</a></li>
      </ul></article>
      <article class="validation-card"><h2>{{ t.limitations }}</h2><p>{{ activeVariable?.limitations }}</p><p>{{ t.disclaimer }}</p></article>
    </main>

    <main v-if="page === 'about'" class="content-page about-page">
      <div class="content-heading"><span class="eyebrow">{{ t.footerProject }}</span><h1>{{ t.aboutTitle }}</h1><p>{{ t.aboutText }}</p></div>
      <section class="validation-card"><h2>{{ t.notOfficial }}</h2><p>{{ locale === 'fr' ? 'L’application calcule des tendances descriptives sur les séries NASA prétraitées. Elle ne fournit ni prévision ni attribution causale.' : 'The application calculates descriptive trends from processed NASA records. It does not provide forecasts or causal attribution.' }}</p><p>{{ t.disclaimer }}</p></section>
      <section class="validation-card"><h2>{{ t.data }} · NASA</h2><p>{{ t.dataScope }}</p><ul class="credits-list"><li v-for="item in catalogVariables" :key="item.id"><span><strong>{{ locale === 'fr' ? item.name_fr : item.name }}</strong> · {{ item.source }} <small>{{ statusLabel(item.status) }} · {{ item.period }}<span v-if="item.short_name"> · CMR: {{ item.short_name }}</span></small></span><a v-if="item.doi" :href="`https://doi.org/${item.doi}`" target="_blank" rel="noreferrer">DOI ↗</a></li></ul></section>
      <section class="validation-card"><h2>{{ t.supportingData }}</h2><ul class="credits-list">
        <li><span><strong>NASA GIBS · Blue Marble: Next Generation</strong><small>{{ t.basemapRole }}</small></span><a href="https://nasa-gibs.github.io/gibs-api-docs/access-basics/" target="_blank" rel="noreferrer">GIBS ↗</a></li>
        <li><span><strong>NASA GISS · Published global monthly temperature series</strong><small>{{ t.validationRole }}</small></span><a href="https://data.giss.nasa.gov/gistemp/data_v4.html" target="_blank" rel="noreferrer">GISTEMP data ↗</a></li>
      </ul><a href="https://science.nasa.gov/earth/earth-observatory/blue-marble-next-generation/" target="_blank" rel="noreferrer">NASA Blue Marble product background ↗</a></section>
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
        <template v-if="wizardStep === 1"><h2 id="wizard-title">{{ t.theme }}</h2><div class="choice-grid"><button v-for="choice in wizardThemeOptions" :key="choice.id" :class="{ chosen: wizardTheme === choice.id }" @click="chooseWizardTheme(choice.id)">{{ choice.label }}</button></div></template>
        <template v-else-if="wizardStep === 2"><h2 id="wizard-title">{{ t.where }}</h2><label class="field-label" for="wizard-place">{{ t.place }}</label><input id="wizard-place" :value="wizardPlace" class="text-input wizard-place-display" readonly aria-readonly="true" /><div class="quick-places"><button v-for="region in regions" :key="region.id" :class="{ chosen: wizardRegionId === region.id }" @click="wizardRegionId = region.id">{{ locale === 'fr' ? region.name_fr : region.name }}</button></div></template>
        <template v-else><h2 id="wizard-title">{{ t.variable }}</h2><div class="wizard-variable-options"><button v-for="item in wizardVariables" :key="item.id" type="button" :disabled="!isWizardVariableReady(item.id)" :class="{ chosen: wizardVariableId === item.id }" @click="wizardVariableId = item.id"><span><strong>{{ locale === 'en' ? item.name : item.name_fr }}</strong><small>{{ item.unit }} · {{ item.source }} · {{ item.period }}</small><small v-if="!isWizardVariableReady(item.id)" class="wizard-pending">{{ statusLabel(item.status) }} · {{ item.status_detail }}</small></span><b v-if="wizardVariableId === item.id" aria-hidden="true">✓</b></button><p v-if="!wizardVariables.length" class="field-help">{{ t.noAvailableVariables }}</p></div><div v-if="wizardVariable" class="wizard-variable"><p>{{ locale === 'en' ? wizardVariable.definition : wizardVariable.definition_fr }}</p></div></template>
        <div class="dialog-actions"><button class="button secondary" :disabled="wizardStep === 1" @click="wizardStep--">{{ locale === 'en' ? 'Back' : 'Retour' }}</button><button class="button primary" :disabled="wizardStep === 3 && !wizardVariableReady" @click="wizardNext">{{ wizardStep === 3 ? t.apply : locale === 'en' ? 'Continue' : 'Continuer' }} <span aria-hidden="true">→</span></button></div>
      </section>
    </div>

    <div v-if="showDemos" class="modal-backdrop" role="presentation" @click.self="showDemos = false">
      <section class="dialog demos-dialog" role="dialog" aria-modal="true" aria-labelledby="demos-title">
        <div class="dialog-top"><div><span class="eyebrow">{{ t.guided }}</span><h2 id="demos-title">{{ t.demoTitle }}</h2></div><button class="icon-button" :aria-label="t.close" @click="showDemos = false">×</button></div>
        <p v-if="demoError" class="demo-error" role="alert">{{ demoError }}</p>
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
