# Pitch — Earth Trends Detective

Document de préparation au pitch et à la démonstration du projet. Le texte décrit l'application et les données locales vérifiées le 13 novembre 2026. Les résultats chiffrés de démonstration peuvent changer si les données ou leur traitement changent : l'écran de l'application reste la référence le jour du pitch.

## L'idée en une phrase

**Earth Trends Detective aide le public à découvrir où une variable de la Terre augmente ou diminue, à quel rythme, et si la tendance est statistiquement convaincante.**

## Pitch oral — environ 90 secondes

> Bonjour. Les satellites et les modèles de la NASA produisent énormément de données sur la Terre. Le problème, c'est qu'il est difficile de savoir quelle variable choisir, où regarder et si le changement observé est réel ou simplement dû aux variations naturelles.
>
> Nous avons créé **Earth Trends Detective**, une application qui transforme ces données en enquête guidée. On choisit une variable — par exemple la température, les précipitations, la végétation ou l'humidité du sol — puis une région et une période. L'application affiche la carte, la série temporelle et le rythme de changement. Elle indique aussi si la tendance est statistiquement significative.
>
> Notre outil permet surtout de comparer une même variable dans des lieux différents. Par exemple, avec l'indice de végétation MODIS et les données actuellement traitées, la tendance estimée est négative dans notre rectangle d'exemple amazonien et positive dans le rectangle du Sahara, entre février 2000 et août 2011. C'est le type de contraste régional que la moyenne mondiale pourrait cacher.
>
> Pour éviter de confondre une saison avec une tendance, nous retirons le cycle saisonnier avant l'analyse et nous présentons plusieurs méthodes statistiques. Nous avons également comparé la moyenne mondiale de notre série GISTEMP avec la série publiée par la NASA.
>
> L'application montre des tendances et leur incertitude ; elle ne prétend pas identifier leur cause. Notre objectif est de rendre l'exploration des données de la Terre plus claire, vérifiable et accessible.

## Version courte — environ 30 secondes

> **Earth Trends Detective transforme les données mensuelles de la NASA en enquête interactive.** L'utilisateur choisit une variable et une région, observe son évolution sur une carte et un graphique, puis consulte le rythme de changement et plusieurs tests statistiques. En comparant deux régions, il peut découvrir qu'une même variable évolue dans des directions différentes. L'outil explique les résultats sans prétendre en connaître la cause.

## Démonstration conseillée — environ 3 minutes

### Avant de commencer

- Ouvrir l'application en français et vérifier que l'API et le front sont lancés.
- Vérifier que la page **Variables** et le parcours **Comparer** répondent correctement.
- Garder la période **Toute la série** pour l'exemple MODIS : sa couverture locale est février 2000–août 2011.
- Ne pas choisir « Depuis 2015 » pour cet exemple : aucune donnée MODIS locale ne couvre cette période.
- Si possible, ouvrir à l'avance les pages **Explorer** et **Comparer** dans deux onglets pour éviter d'attendre les calculs.

### 1. Présenter le choix des données — 20 à 30 secondes

Depuis **Variables**, montrer que l'application ne se limite pas à la température. Le catalogue local expose actuellement huit variables prêtes pour l'analyse :

- température de surface GISTEMP ;
- précipitations GPM ;
- indices de végétation MODIS NDVI et EVI ;
- évaporation MERRA-2 ;
- humidité du sol GLDAS ;
- température de l'air en surface AIRS ;
- dioxyde d'azote troposphérique OMI.

Formulation simple : **« Certaines variables viennent d'instruments satellites, d'autres de modèles ou d'analyses NASA. Le catalogue indique leur source, leur unité et leur période disponible. »**

### 2. Faire une première analyse — environ 1 minute

Dans **Explorer** :

1. Choisir **MODIS NDVI**.
2. Choisir le **rectangle d'exemple de l'Amazonie**.
3. Garder **Toute la série**.
4. Montrer le rectangle sur la carte et la série mensuelle sous la carte.
5. Lire le taux, l'intervalle de confiance et les tests.

À dire : **« Le NDVI est un indice satellitaire lié à l'état de la végétation. Ici, on analyse un rectangle, pas une frontière officielle ni toute l'Amazonie. La série locale va de février 2000 à août 2011. »**

Montrer ensuite la carte : le bleu et le rouge représentent le signe de la pente estimée ; les points signalent les mailles qui ne passent pas le seuil de significativité de la carte après correction FDR. Le fond Blue Marble de NASA GIBS sert uniquement de repère géographique : il ne fournit pas les valeurs analysées.

### 3. Montrer des directions opposées — environ 1 minute

Ouvrir **Comparer**, garder **MODIS NDVI**, puis choisir **Amazonie** et **Sahara**.

Sur les données actuellement traitées, l'OLS estime environ **−0,000625 indice/an** dans le rectangle amazonien et **+0,000413 indice/an** dans le rectangle saharien. Les valeurs p OLS locales sont respectivement inférieures à 0,001. L'écran affiche les résultats recalculés par l'application.

À dire : **« C'est une illustration concrète du défi : la même variable peut présenter des tendances de signes opposés selon la région. Cela ne nous dit pas pourquoi elles diffèrent ; il faudrait une étude scientifique spécifique pour expliquer les causes. »**

### 4. Conclure sur la rigueur — 20 à 30 secondes

À dire : **« Nous retirons le cycle saisonnier avant le calcul de tendance. Nous affichons une pente linéaire, son intervalle de confiance, le test t, Mann–Kendall et le test ajusté de Hamed–Rao. Une tendance non significative reste visible : cela signifie que les données ne donnent pas encore une preuve statistique suffisante, pas qu'il ne se passe rien. »**

## Ce qu'il faut montrer dans l'application

Dans cet ordre, pour relier chaque écran au défi :

1. **Accueil** — expliquer la question : « La Terre change-t-elle, et où ? »
2. **Variables** — montrer le catalogue, les définitions simples, les sources et les périodes réellement disponibles.
3. **Explorer** — sélectionner une variable, une région ou un rectangle dessiné, puis une période couverte par les données.
4. **Carte et graphique** — expliquer la pente sur la carte, le rectangle étudié, la série mensuelle et le retrait des saisons.
5. **Résultats statistiques** — lire la pente, son intervalle de confiance et les valeurs p sans réduire toute l'analyse à un seul voyant « significatif ».
6. **Comparer** — garder la même variable et comparer deux régions pour faire apparaître des différences de signe ou d'amplitude.
7. **Méthodes** — ouvrir cette page si le jury demande comment les calculs sont faits ou validés.
8. **Ressources** — présenter CUAHSI comme un parcours hydrologique complémentaire : il recherche et analyse des observations de stations. Préciser qu'une station est un point de mesure et non une moyenne régionale NASA.

Pour un pitch court, les étapes 1 à 6 suffisent. La page **Méthodes** est utile en réponse aux questions scientifiques ; il n'est pas nécessaire de lire tous les tests pendant la démonstration.

## Les points forts à faire ressortir

- **Plusieurs domaines de la Terre :** température, pluie, végétation, évaporation, humidité du sol, température de l'air et NO₂.
- **Une analyse régionale concrète :** une moyenne mondiale ne masque pas les différences entre lieux.
- **Une chaîne complète :** variable → région → série temporelle → taux de changement → tests statistiques.
- **Une comparaison spatiale :** la même variable peut avoir des directions différentes selon la région.
- **Une interface pensée pour apprendre :** définitions, périodes disponibles, messages lisibles et exemples guidés en français et en anglais.
- **Une lecture honnête :** l'outil distingue données manquantes, couverture temporelle, tendance estimée et significativité ; il ne transforme pas une corrélation en cause.
- **Une validation vérifiable :** la moyenne mondiale GISTEMP de la grille a été comparée à la série mensuelle publiée par NASA GISS. Les chiffres détaillés et le notebook sont dans [`docs/PROGRESS.md`](PROGRESS.md) et [`notebooks/01_validation_gistemp.ipynb`](../notebooks/01_validation_gistemp.ipynb).

## Questions probables du jury

### « Que veut dire statistiquement significatif ? »

Cela signifie que, selon le test et ses hypothèses, les données sont peu compatibles avec l'absence de tendance. Ce n'est ni la probabilité que le résultat soit vrai, ni une preuve de sa cause. Une tendance non significative peut rester intéressante, surtout si la série est courte ou variable.

### « Pourquoi enlever les saisons ? »

Parce que les saisons font monter et baisser régulièrement certaines variables. Les retirer aide à voir l'évolution de fond au fil des années, sans confondre ce cycle régulier avec une tendance de long terme.

### « Comment calculez-vous une valeur régionale ? »

L'application moyenne les cellules de grille qui recouvrent le rectangle, avec une pondération liée à leur latitude. Les cellules sans valeur sont ignorées pour le mois concerné. Le rectangle reste une approximation géographique : il peut inclure une partie d'une zone voisine ou de l'océan.

### « Le rouge signifie-t-il que la situation est mauvaise ? »

Non. Le rouge indique une pente positive et le bleu une pente négative. Le sens favorable ou défavorable dépend de la variable. Les couleurs n'identifient pas une cause.

### « Pourquoi les données s'arrêtent-elles à des dates différentes ? »

Les produits ne commencent pas tous à la même date et n'ont pas tous été acquis sur la même période. L'application montre la couverture disponible pour chaque produit. Par exemple, les séries locales MODIS se terminent en août 2011, AIRS en août 2012 et GISTEMP en septembre 2026. Les périodes non couvertes ne doivent pas être présentées comme analysées.

### « Est-ce que l'application trouve la cause du changement ? »

Non. Elle indique quoi change, où, dans quelle direction et à quel rythme, puis mesure la force statistique de la tendance. Trouver et démontrer la cause demande une analyse scientifique supplémentaire.

### « Quelles sont les limites actuelles ? »

L'analyse porte sur des tendances linéaires mensuelles. Les périodes et les couvertures spatiales varient selon le produit. Les régions prédéfinies et les zones dessinées sont des rectangles. Les tendances statistiques ne démontrent pas un mécanisme causal. Les ressources comme Giovanni, AppEEARS, NASA Hydrology Time Series et NOAA CDO sont proposées comme outils externes avec import de séries ; l'automatisation complète de ces portails n'est pas revendiquée.

### « L'outil est-il déployé en ligne ? »

La version de démonstration fonctionne localement. La préparation au déploiement existe dans le dépôt, mais aucun déploiement public n'est à annoncer tant qu'un serveur, un domaine et une vérification HTTPS ne sont pas disponibles.

## Formule de conclusion

> Earth Trends Detective ne remplace pas les scientifiques. Il donne aux élèves, aux étudiants et au public un moyen simple de poser une question sur la Terre, d'examiner des données réelles et de comprendre à la fois ce que les statistiques montrent — et ce qu'elles ne permettent pas encore de conclure.

## Références internes pour préparer les réponses

- [Cahier des charges et exigences du défi](../AGENT_BRIEF.md), section 1 bis.
- [Méthodes statistiques et limites](METHODS.md).
- [Sources et produits de données](DATA_SOURCES.md).
- [État du projet et validation GISTEMP](PROGRESS.md).
- [Ressources officielles fournies pour le défi](CHALLENGE_RESOURCES.md).
