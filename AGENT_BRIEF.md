# Brief de mission pour l'agent IA : « Détective des tendances du système terrestre »

*NASA Space Apps Challenge 2026 – document à donner tel quel à l'agent (Claude Code ou équivalent)*

> **Mode d'emploi pour l'humain** : placez ce document à la racine du dépôt sous le nom `AGENT_BRIEF.md`, puis donnez à l'agent le prompt de démarrage de la section 18. Les éléments que **vous** devez fournir sont listés en section 3.

## 1. Mission

Tu construis, de bout en bout, un **outil web** pour le NASA Space Apps Challenge 2026, défi *« Devenez un détective des tendances du système terrestre »* (niveau avancé, thèmes Sciences de la Terre et Logiciels).

**Énoncé du défi** : créer un outil capable de sélectionner des variables mesurées par des missions NASA de sciences de la Terre ou produites par des modèles, de visualiser leur évolution dans le temps, et de déterminer **ce qui change, où, dans quelle mesure, et si le changement est statistiquement significatif**. Une même variable peut monter dans une région et baisser dans une autre : l'outil doit le faire voir.

**Le produit final** : une application web où l'utilisateur choisit une variable et une période, voit une **carte mondiale des tendances** (pente + significativité), clique sur un lieu pour voir la **série temporelle décomposée**, compare des **régions aux tendances opposées**, et reçoit un **résumé automatique en langage clair** (quoi / où / combien / significatif ?). La rigueur statistique est le différenciateur n°1.

**Objectif** : gagner. Le jury est composé de scientifiques et d'ingénieurs : ils regardent la rigueur, la validation, la clarté et une démo qui marche.

Liens de référence : défi et soumission https://www.spaceappschallenge.org/ — données NASA https://www.earthdata.nasa.gov/ — guide cloud NASA https://nasa-openscapes.github.io/earthdata-cloud-cookbook/

## 1 bis. Exigences officielles du défi et périmètre (section prioritaire)

Le défi officiel demande une chaîne complète mais simple : choisir une variable et une région, tracer sa série temporelle, mesurer le rythme de changement, puis tester si ce changement est significatif. En cas de conflit entre cette section et la suite du brief, **cette section l'emporte**.

**Les quatre éléments attendus par le défi**

1. **Identifier** des variables de sciences de la Terre susceptibles de montrer une tendance (du simple, comme température et pluie, au plus complexe, comme évaporation ou débit des cours d'eau).
2. **Acquérir** la variable pour **une région précise**, car la plupart des tendances ne sont pas globales.
3. **Générer et visualiser une série temporelle** de la variable pour cette région, sur une période assez longue pour une analyse statistique.
4. **Faire une analyse statistique de base** : taux de changement dans le temps et test de significativité (test t, Mann-Kendall ou intervalles de confiance).

Une réponse qui fait à la fois la visualisation et l'analyse couvre tout le périmètre du défi.

**Public visé** : lycéens, étudiants et grand public ayant un peu de bagage scientifique. Le défi suggère des définitions simples des variables, un parcours de « détective de données » (quelques questions sur ce que l'on veut étudier et où) et quelques démonstrations à regarder.

**Indications officielles à respecter**

- Résolutions disponibles : horaire, 3-horaire, quotidienne, mensuelle. **Quotidien et mensuel sont les plus faciles** : le mensuel est le défaut, le quotidien est optionnel.
- Une tendance est **intéressante même si elle n'est pas significative** : parfois une période plus longue suffit à la rendre significative. L'outil doit le dire clairement.
- Les **cycles réguliers** (saisons) doivent être retirés pour voir la tendance.
- Les tendances **non linéaires** sortent du périmètre : détecter et analyser des **tendances linéaires** est un très bon départ.
- Instruments et modèles cités : MODIS, OMI, AIRS, GPM, MERRA-2, GLDAS.
- Exemples de régions : désert, forêt tropicale, estuaire à marée, atmosphère au-dessus d'une grande ville.
- Outils externes possibles, par exemple le consortium CUAHSI pour l'hydrologie : https://www.cuahsi.org/
- Les ressources officielles de l'onglet **Resources** de la page du défi sont annoncées pour le 13 novembre, pas avant. Ne les attends pas : avance avec les sources de ce brief. Quand elles sortent, l'humain les copie dans `docs/CHALLENGE_RESOURCES.md`. Tu les lis alors et tu complètes le catalogue, les jeux de données et les démos si elles apportent quelque chose.

**Ce que cela change pour le plan**

1. **Le cœur du MVP est : variable + région → série temporelle → pente + test de significativité.** La carte mondiale sert à repérer *où* regarder, elle ne suffit pas seule.
2. **Deux niveaux d'analyse** : *Base* (régression linéaire avec test t et IC 95 %, Mann-Kendall et pente de Sen), toujours affiché ; *Rigoureux* (correction d'autocorrélation Hamed-Rao, FDR, rupture), en option et expliqué simplement.
3. **Parcours guidé** en quelques questions, définitions simples, info-bulles sur les termes statistiques, et **deux démos guidées** jouables dans l'application.
4. **Régions** : régions prédéfinies (désert, forêt tropicale, estuaire, grande ville…) et dessin libre, avec moyenne pondérée par la surface. Stocker les données en Zarr chunké pour lire une emprise rapidement (temps complet, blocs spatiaux d'environ 30 x 30 mailles).
5. **Tendance non significative** : afficher « pas (encore) significatif », expliquer ce que cela veut dire et montrer l'effet d'une période plus longue ou plus courte.
6. **Priorité des variables** : couvrir plusieurs domaines du défi avant les fonctions différenciatrices : GISTEMP pour le climat, MERRA-2/GLDAS/GPM pour précipitations et eau terrestre, MODIS pour la végétation, puis AIRS/OMI pour atmosphère et qualité de l'air. GISTEMP reste le premier jeu ingéré et validé, mais ne constitue pas à lui seul le produit final.

**Décision de portée (mise à jour par le responsable du projet, 2026-11-01)** : la version livrable doit analyser plusieurs variables NASA, et non un MVP limité à GISTEMP. Viser au minimum trois variables réellement acquises, validées et analysables, dont GISTEMP et des mesures couvrant au moins deux autres domaines du défi. Continuer avec toutes les variables prioritaires dont l'accès, le volume et les ressources de calcul le permettent. Une variable ne compte comme prise en charge qu'après acquisition réelle, citation NASA complète, prétraitement, analyse, API, interface et tests ; une simple entrée de catalogue ne compte pas.

## 2. Règles de travail (obligatoires)

1. **Autonomie, mais pas d'invention.** Ne fabrique jamais de données, de chiffres, de références ou de liens. Si une donnée est inaccessible, dis-le et applique le plan B prévu.
2. **Vérifie avant d'utiliser.** Les noms de produits NASA (`short_name`), URLs et versions changent : confirme-les par une requête réelle (CMR/earthaccess) avant de les écrire dans le code ou la doc.
3. **Produit multi-variable d'abord.** GISTEMP est la première chaîne de référence, pas une limite de portée ni un prérequis de déploiement avant les autres variables. Étendre ensuite le même parcours complet aux produits prioritaires vérifiés par CMR/Earthdata : données réelles, Zarr, tendances, carte, API, interface et tests. Aucun produit non vérifié ne doit être affiché comme disponible.
4. **Reproductibilité.** Tout se lance par des commandes documentées (`make`/scripts). Versions épinglées. Graines aléatoires fixées.
5. **Tests.** Chaque module statistique a des tests. Pas de fusion de code qui casse les tests.
6. **Petits commits** avec messages clairs. Une branche par jalon, merge sur `main` quand le jalon est validé.
7. **Secrets** : jamais dans le dépôt. Utilise `.env` (ignoré par git) et fournis un `.env.example`.
8. **Journal de bord** : tiens à jour `docs/PROGRESS.md` (ce qui est fait, ce qui reste, décisions, problèmes).
9. **Quand tu es bloqué** (identifiants, serveur, décision de produit), arrête-toi sur ce point, explique précisément ce qu'il te faut, et continue sur une autre tâche indépendante.
10. **Honnêteté scientifique** : affiche les limites (résolution, couverture, période courte, corrélation ≠ causalité). Ne surinterprète pas.
11. **Attribution** : cite chaque jeu de données NASA utilisé (nom, DOI, version) dans l'application et dans `docs/DATA_SOURCES.md`.

## 3. Ce que l'humain doit fournir

| Élément | Pourquoi | Où |
| --- | --- | --- |
| Compte Earthdata (login/mot de passe) | Télécharger les données NASA | https://urs.earthdata.nasa.gov/ |
| Dépôt GitHub (public, licence MIT ou Apache-2.0) | Code et livrable | https://github.com/ |
| Accès au serveur (SSH, domaine, ports 80/443) | Déploiement | à fournir |
| Décisions de contenu (nom du produit, logo, noms de l'équipe) | Branding et page projet | à fournir |
| Contenu de l'onglet Resources du défi (à partir du 13 novembre) | Ressources officielles, annoncées pour le 13 novembre (pas encore disponibles ; ne bloque pas le démarrage) | Page du défi sur spaceappschallenge.org, à copier dans docs/CHALLENGE\_RESOURCES.md |

Pour `earthaccess`, les identifiants se donnent via variables d'environnement `EARTHDATA_USERNAME` / `EARTHDATA_PASSWORD` ou le fichier `~/.netrc`. Doc : https://earthaccess.readthedocs.io/

## 4. Stack imposée (ne pas en changer sans raison forte)

| Couche | Choix | Lien |
| --- | --- | --- |
| Langage data/API | Python 3.11+ | https://www.python.org/ |
| Gestion d'env | `uv` | https://docs.astral.sh/uv/ |
| Accès données NASA | `earthaccess` (+ Harmony/OPeNDAP si utile) | https://earthaccess.readthedocs.io/ |
| Tableaux N-D | `xarray`, `dask`, `zarr`, `netcdf4`/`h5netcdf` | https://docs.xarray.dev |
| Stats | `numpy`, `scipy`, `numba`, `statsmodels`, `pymannkendall` (référence de test) | https://github.com/mmhs013/pyMannKendall |
| Régridding (si besoin) | `xesmf` ou `xarray.interp` | https://xesmf.readthedocs.io/ |
| Tuiles raster | `rio-tiler` (pré-génération) ou `titiler` | https://developmentseed.org/titiler/ |
| API | FastAPI + Uvicorn + Pydantic | https://fastapi.tiangolo.com/ |
| Frontend | Vue 3 + Vite + TypeScript, MapLibre GL JS, Apache ECharts | https://maplibre.org/maplibre-gl-js/docs/ — https://echarts.apache.org/ |
| Déploiement | Docker Compose + Caddy (HTTPS auto) | https://caddyserver.com/ |
| Qualité | `pytest`, `ruff`, `mypy` (léger), `eslint`, `vitest` |  |

Pas de Redis dans le MVP (le précalcul fait la vitesse). Ne l'ajoute que si un besoin mesuré apparaît.

## 5. Structure du dépôt à créer

```
repo/
  AGENT_BRIEF.md
  README.md              # EN (principal) + résumé FR
  Makefile
  docker-compose.yml
  .env.example
  data/
    catalog.yaml         # catalogue curé des variables
    raw/                 # ignoré par git
    processed/           # Zarr + GeoTIFF, ignoré par git
    tiles/               # ignoré par git
  pipeline/
    ingest/              # un module par jeu de données
    preprocess/          # grille commune, anomalies, masque
    trends/              # sen, mk, hamed-rao, fdr, pettitt, stl
    tiling/
    cli.py               # commandes: ingest, preprocess, trends, tiles
  api/
    app/ (main.py, routes/, schemas.py, services/, summary.py)
    tests/
  web/
    src/ (components/, views/, stores/, i18n/)
  notebooks/
    01_validation_gistemp.ipynb
    02_synthetic_tests.ipynb
  docs/
    METHODS.md  DATA_SOURCES.md  PROGRESS.md  DEMO_SCRIPT.md  PITCH_OUTLINE.md
  deploy/
    Caddyfile
```

## 6. Préparation de l'environnement (jalon M0)

- Initialiser le dépôt, `uv init`, `pyproject.toml`, `Makefile` (cibles : `setup`, `ingest`, `preprocess`, `trends`, `tiles`, `test`, `dev`, `build`).
- Configurer `ruff`, `pytest`, GitHub Actions minimale (lint + tests) : https://docs.github.com/actions
- Vérifier la connexion NASA : `earthaccess.login()` puis une recherche simple.
- **Critère d'acceptation M0** : `make setup && make test` passe sur une machine propre ; `earthaccess.login()` réussit.

## 7. Catalogue des variables (`data/catalog.yaml`)

Format par entrée :

```yaml
- id: gistemp_tas_anom
  name: Surface temperature anomaly
  name_fr: Anomalie de température de surface
  source: NASA GISS GISTEMP v4
  doi: ...            # à vérifier
  unit: °C
  frequency: monthly
  grid: 2x2 deg
  period: 1880-present
  higher_is: warming  # sens d'interprétation de la hausse
  description: ...
  description_fr: ...
  limitations: ...
  access: {type: url|earthaccess, ref: ...}
```

### Jeux de données (priorités)

Les priorités ci-dessous sont des cibles, pas des `short_name` confirmés. Avant intégration, effectuer une requête réelle `earthaccess.search_datasets`, sélectionner une version adaptée, inspecter sa variable scientifique et sa temporalité, puis vérifier ses URLs de service et l'accès à des granules. Inscrire uniquement les valeurs obtenues dans le catalogue. Toute variable disponible doit suivre le parcours complet multi-variable ; si l'accès ou les ressources manquent, noter le blocage et continuer les autres.

| Priorité | Variable | Source | Lien |
| --- | --- | --- | --- |
| **P0** | Anomalie de température de surface (référence de validation) | GISTEMP | https://data.giss.nasa.gov/gistemp/ |
| **P0** | Température à 2 m et précipitations/évaporation de surface (produits mensuels) | MERRA-2 | https://gmao.gsfc.nasa.gov/reanalysis/MERRA-2/ |
| **P0** | Humidité du sol, évapotranspiration ou ruissellement (produit mensuel) | GLDAS | https://ldas.gsfc.nasa.gov/gldas |
| **P0** | Précipitations mensuelles | GPM IMERG | https://gpm.nasa.gov/data/imerg |
| **P1** | Végétation (NDVI/EVI mensuel) | MODIS MOD13 | https://lpdaac.usgs.gov/products/mod13a3v061/ |
| **P1** | Température ou humidité atmosphérique mensuelle | AIRS | https://airs.jpl.nasa.gov/ |
| **P1** | Ozone ou dioxyde d'azote | OMI | https://aura.gsfc.nasa.gov/omi.html |
| P2 | Masse d'eau terrestre | GRACE / GRACE-FO | https://grace.jpl.nasa.gov/ |
| P3 | Glace de mer | NSIDC | https://nsidc.org/data/g02135 |
| P3 | CO₂ | OCO-2 / OCO-3 | https://oco.jpl.nasa.gov/ |

**Règles d'accès** :

- **GISTEMP** : le fichier NetCDF grillé est téléchargeable directement depuis la page GISTEMP (section données). Trouve l'URL exacte sur la page et vérifie le format (grille 2°x2°, mensuel, anomalies).
- **Autres** : cherche avec `earthaccess.search_datasets(keyword=...)` et récupère le `short_name` réel avant tout téléchargement. Doc CMR : https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
- **Gros jeux (IMERG, MODIS)** : agrège au mois et sous-échantillonne à une grille de 1° ou 2° le plus tôt possible. Utilise Harmony (https://harmony.earthdata.nasa.gov/docs) ou OPeNDAP pour ne pas télécharger tout. Si trop lourd, réduis la période ou l'emprise et documente-le.
- **GIBS** (https://nasa-gibs.github.io/gibs-api-docs/) = **imagerie de fond uniquement**, jamais source de valeurs scientifiques.
- **Plan B** : si un jeu de données échoue après deux tentatives raisonnables, passe au suivant et note-le dans `PROGRESS.md`. Trois variables solides valent mieux que sept bancales.

**MERRA-2 et GLDAS** sont des produits mensuels hébergés au GES DISC (https://disc.gsfc.nasa.gov/). Récupère le `short_name` réel avec `earthaccess`, puis sous-échantillonne (variables utiles, grille de 1°, emprise) avec Harmony ou OPeNDAP au lieu de tout télécharger.

**Giovanni** (https://giovanni.gsfc.nasa.gov/giovanni/) génère des séries temporelles régionales : utilise-le comme **référence de validation** de tes propres séries.

**Résolution** : mensuel par défaut pour toutes les variables. L'interface et les méthodes doivent exposer pour chaque variable sa période, sa fréquence, son unité, sa grille native et ses limites ; les conversions et ré-échantillonnages doivent rester documentés.

## 8. Prétraitement (jalon M1)

Pour chaque variable, `pipeline preprocess <id>` doit produire un **Zarr** standardisé :

1. **Grille commune** : 2° pour GISTEMP (natif), 1° ou 2° pour les autres. Dimensions `time, lat, lon`, longitudes en \[-180, 180\], latitudes croissantes. CRS EPSG:4326.
2. **Calendrier mensuel** : agrégation au mois si nécessaire ; temps normalisés au 1er du mois.
3. **Masque et valeurs manquantes** : `NaN` explicites. Un pixel est **valide** s'il a au moins 70 % de mois valides et au moins 10 ans de données. Sauvegarder `n_valid`.
4. **Anomalies désaisonnalisées** : retirer la climatologie mensuelle (`ds.groupby('time.month') - ds.groupby('time.month').mean('time')`) calculée sur la fenêtre d'analyse (sauf GISTEMP, déjà en anomalies).
5. **Chunking** : un jeu « série temporelle par pixel » (chunks `time` complet, `lat/lon` petits) pour la lecture au clic.
6. **Métadonnées** : unité, source, DOI, version, date de traitement, paramètres, dans les `attrs` du Zarr.

**Critère d'acceptation M1** : pour GISTEMP, le Zarr s'ouvre avec `xarray`, a les bonnes dimensions, la moyenne globale pondérée par cos(lat) reproduit l'allure publiée de GISTEMP, et un test automatique vérifie les dimensions, l'absence de longitudes en 0–360 et la présence des attributs.

## 9. Moteur statistique (jalon M2) — spécification détaillée

Le code vit dans `pipeline/trends/`. Il doit être **vectorisé** (numpy + numba `@njit(parallel=True)`) et appelé via `xr.apply_ufunc` avec `dask='parallelized'`.

### 9.1 Méthode principale (par pixel, sur anomalies mensuelles)

| Niveau | Sorties | Méthode | Référence |
| --- | --- | --- | --- |
| Base | `slope_ols`, `slope_ols_lo`, `slope_ols_hi`, `p_ols` | Régression linéaire sur anomalies mensuelles, pente en unité par an, IC 95 %, test t sur la pente | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html |
| Base | `slope`, `slope_lo`, `slope_hi` | Pente de Sen avec IC 95 % | https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.theilslopes.html |
| Base | `p_mk` | Test de Mann-Kendall classique | https://github.com/mmhs013/pyMannKendall |
| Rigoureux | `p_value` | Mann-Kendall modifié de Hamed-Rao (correction d'autocorrélation) | https://doi.org/10.1016/S0022-1694(97)00125-X |
| Rigoureux | `significant_fdr` | Contrôle du FDR sur tous les pixels valides (cartes) | https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html |
| Les deux | `n_valid` | Nombre de mois valides | Comptage direct |

Le niveau **Base** est toujours affiché, car le public visé est composé de lycéens et d'étudiants : régression linéaire avec test t, puis Mann-Kendall et pente de Sen. Le niveau **Rigoureux** est un mode avancé : il corrige le fait que des mois successifs se ressemblent (ce qui rend les tests simples trop optimistes) et contrôle les faux positifs sur la carte. Si les deux niveaux ne donnent pas le même verdict, l'interface l'indique.

### 9.2 Règles

- **Pas de test sur une tendance STL** (autocorrélation → p-values trop optimistes). STL sert seulement à la **visualisation** (cycle saisonnier, tendance lissée) dans le panneau d'un point : https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.STL.html
- **Tests multiples** : appliquer Benjamini-Hochberg avec `alpha_FDR = 0.10` (équivalent à un seuil global \~0.05 selon la recommandation de Wilks 2016, https://doi.org/10.1175/BAMS-D-15-00267.1). Documenter ce choix dans `METHODS.md`. Si l'autocorrélation spatiale est forte, discuter Benjamini-Yekutieli comme variante plus conservatrice.
- **Robustesse** : option `--annual` qui refait l'analyse sur moyennes annuelles et compare le signe/la significativité (carte de concordance).
- **Fenêtres temporelles précalculées** : `full` (toute la période), `2010-fin`, `2015-fin`. Elles servent à montrer la **sensibilité à la période**.
- **Moyennes régionales** : pondération par `cos(lat)`, `NaN` ignorés explicitement.
- **Rupture (Pettitt)** : calculée **à la demande** pour un point ou une région (pas sur toute la grille) : https://github.com/mmhs013/pyHomogeneity
- **Tendances opposées** : produire (a) une carte des classes `{hausse significative, baisse significative, non significatif}`, (b) un clustering simple des régions par signe/amplitude, (c) optionnel : EOF/PCA (https://ajdawson.github.io/eofs/) pour mettre en évidence des dipôles.

### 9.3 Sorties

Par variable et par fenêtre : un **GeoTIFF/COG** et un **Zarr** contenant `slope`, `slope_lo`, `slope_hi`, `p_value`, `significant_fdr`, `n_valid`, `sign_class`. Nom : `data/processed/<id>/trend_<window>.zarr`.

### 9.4 Tests obligatoires (`pipeline/trends/tests/`)

1. **Séries synthétiques** : tendance connue (ex. +0,02/an) + bruit gaussien + AR(1) ; la pente retrouvée est à ±5 % ; sans tendance, le taux de faux positifs reste proche du seuil.
2. **Équivalence** avec `pymannkendall` (version Hamed-Rao) et `scipy.stats.theilslopes` sur 1000 pixels aléatoires (tolérance 1e-6 pour la pente, 1e-4 pour la p-value). Si l'écart est plus grand, corrige ton implémentation vectorisée.
3. **Valeurs manquantes** : pixels avec trous, pixels entièrement `NaN`, séries constantes (pas d'exception, résultat `NaN` explicite).
4. **FDR** : vérifie que le nombre de pixels significatifs après FDR est ≤ avant correction.
5. **Performance** : temps de calcul d'une grille 2°x2° (≈ 16 000 pixels, \~ 1700 mois) < 2 minutes sur un portable ; documenter le temps pour 1°.

**Critère d'acceptation M2** : tous les tests passent ; `METHODS.md` décrit chaque méthode avec formules, hypothèses et limites.

## 10. Validation scientifique (jalon M3)

Dans `notebooks/01_validation_gistemp.ipynb` :

- Calculer la tendance **globale** (moyenne pondérée) de GISTEMP sur 1980–fin et comparer à la valeur publiée par la NASA GISS (page https://data.giss.nasa.gov/gistemp/). Afficher l'écart.
- Vérifier **qualitativement** les motifs régionaux connus (amplification arctique, réchauffement plus fort sur les continents que sur les océans).
- Pour GRACE (si disponible) : comparer qualitativement avec les zones publiées d'assèchement (aquifères, calottes) et d'humidification : https://grace.jpl.nasa.gov/
- Produire un tableau « attendu vs obtenu » avec **sources citées**. Ne rien affirmer sans source.
- Intégrer ce résumé dans la page **Méthodes et validation** de l'application.

**Validation croisée avec Giovanni** : pour deux ou trois régions et variables, génère la série régionale dans Giovanni (https://giovanni.gsfc.nasa.gov/giovanni/) et compare-la à celle de ton outil. Documente l'écart (pondération, grille, masque) dans le notebook.

## 11. Cartes et tuiles (jalon M4)

- Générer des **tuiles raster XYZ** (zooms 0 à 5 suffisent pour une grille de 1–2°) avec `rio-tiler`, deux couches par fenêtre : **pente** (palette divergente centrée sur 0) et **significativité** (masque pour le *stippling*).
- **Palette divergente centrée sur zéro, adaptée au daltonisme** (par ex. Crameri *vik*/*berlin* : https://www.fabiocrameri.ch/colourmaps/ ou ColorBrewer : https://colorbrewer2.org/). Échelle symétrique, bornes fixées par un percentile (ex. 98e) pour éviter l'écrasement par les extrêmes.
- Sortie : `data/tiles/<id>/<window>/{z}/{x}/{y}.png`. Alternative acceptable : servir via `titiler`.
- Si le rendu des tuiles bloque, **plan B** : renvoyer la grille en binaire compressé (≈ 16 000 à 65 000 valeurs) et la dessiner avec MapLibre/deck.gl côté client (https://deck.gl/).

## 12. API (jalon M5)

FastAPI, schémas Pydantic, documentation OpenAPI auto (`/docs`). CORS limité au domaine du site.

| Endpoint | Rôle |
| --- | --- |
| `GET /api/variables` | Catalogue : id, noms FR/EN, unité, **définition en une phrase**, période, limites, fenêtres disponibles |
| `GET /api/suggest?theme=&place=` | Parcours guidé : à partir des réponses de l'utilisateur, propose des variables et des régions (règles simples, pas de LLM) |
| `GET /api/regions` | Régions prédéfinies (désert, forêt tropicale, estuaire, grande ville…) avec polygone et description simple |
| `POST /api/region` | **Cœur du produit** : variable + région (polygone ou prédéfinie) + période → série mensuelle pondérée par la surface, anomalies, cycle saisonnier, tendance Base (MCO + test t, Mann-Kendall + Sen, IC 95 %) et Rigoureuse, rupture, résumé |
| `GET /api/trend/{variable}?window=` | Métadonnées de la couche carte, URLs de tuiles, bornes de palette, stats globales |
| `GET /api/point?variable=&lat=&lon=&start=&end=` | Même analyse pour un point cliqué (mêmes sorties que `/api/region`) |
| `GET /api/compare?variable=&a=&b=` | Deux régions ou points côte à côte : séries, tendances et résumé de contraste |
| `GET /api/export?...` | CSV (séries), GeoTIFF/PNG (cartes) |
| `GET /api/health` | Vérification de service |

**Exemple de réponse `/api/point` (forme cible)** :

```json
{
  "variable": "gistemp_tas_anom",
  "location": {"lat": 70.0, "lon": 20.0},
  "period": {"start": "1990-01", "end": "2024-12"},
  "trend": {"slope": 0.045, "slope_lo": 0.038, "slope_hi": 0.052, "unit": "°C/an"},
  "p_value": 0.0003,
  "significant": true,
  "break": {"date": "2005-06", "p": 0.01},
  "series": {"time": ["..."], "value": [0.1], "seasonal": [0.0], "trend": [0.1]},
  "summary": {"fr": "...", "en": "..."},
  "caveats": ["..."]
}
```

**Résumé automatique** (`api/app/summary.py`) : **gabarits déterministes**, pas de LLM à l'exécution (reproductible, rapide, sans dérive). Il doit répondre à : *quoi* (variable), *où* (lieu/région), *combien* (pente avec IC et unité), *significatif ?* (p-value, correction), et ajouter la rupture éventuelle et une mise en garde si la période est courte. Textes en **FR et EN**.

**Tests API** : `pytest` + `httpx` ; contrats de schéma ; temps de réponse `/api/point` < 300 ms en local.

**Critère d'acceptation M5** : tous les endpoints répondent avec les bons schémas ; tests verts ; `/docs` utilisable.

## 13. Frontend (jalons M6 puis M7)

**Langue** : interface **EN par défaut avec bascule FR** (jury international). Accessibilité : contraste suffisant, légendes avec unités, aucune information portée par la couleur seule, texte alternatif, lisible sur mobile.

**Public visé** : lycéens, étudiants et grand public avec un peu de bagage scientifique. Chaque variable a une **définition en une phrase**. Chaque terme statistique (tendance, p-value, intervalle de confiance, significatif) a une **info-bulle en langage simple**. Les résumés évitent le jargon.

### M6 – Explorateur multi-variable (écrans indispensables)

1. **Assistant « détective »** : deux ou trois questions (quel thème : climat, eau, végétation, air ? quel lieu : région prédéfinie ou à dessiner ?) qui proposent des variables avec leur définition simple.
2. **Sélecteur de variable** alimenté par le catalogue des produits réellement intégrés : description, unité, période, fréquence, résolution et limites. Les variables annoncées mais pas encore accessibles restent identifiées comme indisponibles et ne déclenchent pas de fausse analyse.
3. **Choix de la région** : régions prédéfinies (désert, forêt tropicale, estuaire, grande ville…) ou rectangle/polygone dessiné sur la carte.
4. **Série temporelle de la région** (ECharts) : série brute, cycle saisonnier retiré (anomalies), droite de tendance, période réglable.
5. **Résultats statistiques en clair** : pente avec IC 95 %, test t et Mann-Kendall, verdict « significatif » ou « pas (encore) significatif », phrase quoi / où / combien / significatif. Si le résultat n'est pas significatif, expliquer qu'une période plus longue pourrait changer le verdict.
6. **Carte des tendances** pour voir *où* ça change : fond GIBS, couche de pente en palette divergente centrée sur 0, stippling des zones non significatives, légende ; un clic ouvre la série du point.
7. **Fenêtres de période** (complète, 2010-fin, 2015-fin) pour montrer la sensibilité de la tendance.
8. **Deux démos guidées** : boutons « regarder un exemple » qui rejouent un parcours complet pas à pas.
9. **Page Méthodes et validation** et crédits NASA.

### M7 – Fonctions avancées (après le déploiement de l'explorateur multi-variable)

10. **Mode « tendances opposées »** : carte des classes de signe et comparaison de deux régions (clic ou polygone).
11. **Mode Rigoureux** dans l'interface (autocorrélation, FDR) avec explication simple.
12. **Détection de rupture** affichée sur le graphique.
13. **Export** (CSV, PNG, GeoTIFF).
14. **Extension facultative** aux produits P2/P3 non intégrés et aux données quotidiennes.

**Performances** : rendu carte fluide ; premier affichage < 3 s ; clic point < 1 s. Tests `vitest` sur les stores et utilitaires ; un test de bout en bout léger (Playwright, https://playwright.dev/) sur le parcours principal si le temps le permet.

## 14. Déploiement (jalon M8)

- `docker-compose.yml` avec : `api` (FastAPI), `web` (build statique servi par Caddy), `caddy` (HTTPS auto), volume pour `data/processed` et `data/tiles` en lecture seule.
- `deploy/Caddyfile` : domaine fourni par l'humain, reverse proxy `/api` vers FastAPI, fichiers statiques et tuiles avec cache long.
- Ouvrir seulement 80 et 443. Ne pas exposer d'autres services. Pas de secrets dans les images.
- Script `make deploy` (ou `deploy/deploy.sh`) : build, envoi des données dérivées, `docker compose up -d`.
- **Précalcul sur la machine de développement**, puis envoi des **résultats seulement** (pas les fichiers NASA bruts) vers le serveur.
- **Vérifications** : site accessible en HTTPS depuis un téléphone en 4G ; redémarrage automatique (`restart: unless-stopped`) ; page chargée en moins de 3 s.
- **Plan B** : si le serveur n'est pas prêt, déployer le frontend sur Vercel/Netlify (https://vercel.com/, https://www.netlify.com/) et l'API sur Render/Fly.io (https://render.com/, https://fly.io/).

**Critère d'acceptation M8** : URL publique fonctionnelle, parcours principal testé de bout en bout sur la version déployée.

## 15. Documentation et livrables du concours (jalon M9)

Vérifie les consignes exactes sur https://www.spaceappschallenge.org/ (format, durée de vidéo, champs du formulaire) et adapte.

**À produire dans le dépôt** :

- `README.md` (EN principal + résumé FR) : problème, solution, captures, installation en 5 commandes, architecture, données utilisées, méthodes, limites, licences, équipe.
- `docs/METHODS.md` : méthodes statistiques, formules, hypothèses, choix (FDR, Hamed-Rao, anomalies), limites.
- `docs/DATA_SOURCES.md` : chaque jeu de données (nom, DOI, version, URL, date d'accès, traitement).
- `docs/DEMO_SCRIPT.md` : script minuté de la démo.
- `docs/PITCH_OUTLINE.md` : plan de présentation de 5 à 7 minutes.
- `notebooks/` reproductibles avec sorties enregistrées.

**Trois scénarios de démo** (à choisir selon les données réellement disponibles et validées) :

1. **Eau terrestre (GRACE)** : assèchement dans certaines régions, humidification dans d'autres.
2. **Glace de mer** : déclin arctique et comportement différent en Antarctique, avec forte dépendance à la période.
3. **Végétation ou pluie** : verdissement ici, brunissement ailleurs.

Si une variable n'est pas prête, remplace-la par un scénario GISTEMP (ex. amplification arctique, contraste continent/océan, sensibilité de la tendance à la période).

Chaque scénario est aussi une **démo guidée** jouable dans l'application (le défi recommande des exemples à regarder). Pour chacun : une région nommée, une variable, une phrase de contexte **sourcée** et le verdict statistique. Prévois au moins un cas **non significatif** expliqué, par exemple à cause d'une période trop courte.

**Plan de présentation (5 à 7 min)** : accroche (carte avec tendances opposées) → problème → solution en une phrase → **démo en direct 2–3 min** (variable → carte → deux régions opposées → résumé auto → changement de période) → rigueur scientifique (anomalies, Hamed-Rao, pente de Sen + IC, FDR, validation) → impact et suite → sources.

**Questions probables du jury** (préparer les réponses dans `PITCH_OUTLINE.md`) : autocorrélation, tests multiples, pente de Sen vs régression linéaire, sensibilité à la période, validation, limites des données, corrélation ≠ causalité.

## 16. Jalons, ordre et priorités

| Jalon | Contenu | Priorité |
| --- | --- | --- |
| M0 | Dépôt, environnement, accès Earthdata | MVP |
| M1 | Ingestion et prétraitement **GISTEMP** (Zarr), premier adaptateur de données | MVP |
| M1b | Intégration multi-variable des produits P0/P1 vérifiés et accessibles (MERRA-2, GLDAS, GPM, MODIS, AIRS, OMI selon ressources) | MVP |
| M2 | Séries régionales pondérées et moteur commun : tendance Base (MCO + test t, Mann-Kendall + Sen, IC), niveau Rigoureux et tests par variable/unité | MVP |
| M3 | Validation (GISS, Giovanni) et notebook | MVP |
| M4 | Tuiles et palette | MVP |
| M5 | API, dont `/region`, `/regions`, `/suggest` | MVP |
| M6 | Frontend multi-variable : sélecteur catalogue, assistant, régions, séries, résultats, cartes et deux démos guidées | MVP |
| M8 | **Déploiement de l'explorateur multi-variable** | MVP |
| M7 | Fonctions avancées (mode Rigoureux enrichi, rupture affichée, export avancé, produits P2/P3 restants) | Après M8 |
| M9 | Documentation, vidéo, présentation | Obligatoire |

**Règle** : les fonctions avancées M7 attendent M8, mais l'intégration des variables prioritaires P0/P1 fait partie du produit attendu avant déploiement. Si le temps ou l'accès manque, prioriser au moins trois variables NASA réellement intégrées couvrant plusieurs domaines, puis consigner chaque produit restant comme bloqué avec la raison exacte. Ne jamais afficher un produit inaccessible comme disponible ni fabriquer de données ou de résultats.

## 17. Définition de « terminé »

- [ ] Application accessible en HTTPS, sans connexion, stable
- [ ] Parcours « détective » : un utilisateur sans connaissances choisit une variable et une région
- [ ] Au moins 3 variables NASA (GISTEMP + MERRA-2, GLDAS ou GPM), avec définition simple, unité et limites
- [ ] Série temporelle de la région, cycle saisonnier retiré, droite de tendance
- [ ] Taux de changement avec IC 95 %, test t et Mann-Kendall (+ pente de Sen), verdict clair y compris « pas (encore) significatif »
- [ ] Carte des tendances avec palette divergente centrée sur 0 et stippling
- [ ] Niveau Rigoureux (Hamed-Rao, FDR) documenté et expliqué simplement
- [ ] Résumé automatique quoi / où / combien / significatif en FR et EN
- [ ] Sensibilité à la période démontrée dans l'interface
- [ ] Deux démos guidées, dont un cas de tendances opposées
- [ ] Validation visible (GISS, Giovanni, publications) avec sources
- [ ] Tests verts (pipeline, API, front), CI verte
- [ ] README, METHODS, DATA\_SOURCES, notebooks reproductibles ; toutes les données NASA citées
- [ ] Script de démo, plan de présentation, vidéo ou script de vidéo prêts

## 18. Prompt de démarrage (à copier-coller à l'agent)

```
Lis AGENT_BRIEF.md en entier, en commençant par la section 1 bis (exigences officielles du défi), qui prime en cas de conflit. Tu es l'ingénieur principal de ce projet.
Commence par M0, puis enchaîne M1 à M6 et M8 dans l'ordre pour livrer un
explorateur multi-variable déployé, avec GISTEMP comme première chaîne mais
pas comme unique variable. Intègre les produits prioritaires réellement
accessibles et validés ; vise au moins trois variables couvrant plusieurs
domaines du défi. Respecte les
règles de la section 2 : ne fabrique aucune donnée ni référence, vérifie
chaque URL et chaque short_name par une requête réelle, écris des tests,
fais des commits fréquents et tiens docs/PROGRESS.md à jour. Quand il te
manque un identifiant, un accès serveur ou une décision, dis-le-moi
précisément et continue sur une tâche indépendante. À la fin de chaque
jalon, résume en 5 lignes ce qui est fait, les critères d'acceptation
validés et la suite.
```

## 19. Annexe : liens essentiels

- Défi et soumission : https://www.spaceappschallenge.org/
- Données NASA : https://www.earthdata.nasa.gov/ — recherche : https://search.earthdata.nasa.gov/
- Guide cloud NASA : https://nasa-openscapes.github.io/earthdata-cloud-cookbook/
- CMR API : https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html
- Harmony : https://harmony.earthdata.nasa.gov/docs
- GIBS : https://nasa-gibs.github.io/gibs-api-docs/ — Worldview : https://worldview.earthdata.nasa.gov/
- GISTEMP : https://data.giss.nasa.gov/gistemp/
- Hamed & Rao (1998) : https://doi.org/10.1016/S0022-1694(97)00125-X
- Wilks (2016), field significance : https://doi.org/10.1175/BAMS-D-15-00267.1
- xarray : https://docs.xarray.dev — Zarr : https://zarr.dev
- FastAPI : https://fastapi.tiangolo.com/ — MapLibre : https://maplibre.org/maplibre-gl-js/docs/ — ECharts : https://echarts.apache.org/
