# Présenter Earth Trends Detective — version simple

Ce document est fait pour présenter le projet à des personnes qui le découvrent. Les exemples et les périodes correspondent aux données locales vérifiées le 13 novembre 2026.

## L'idée en une phrase

**Notre application aide à voir comment un indicateur de la Terre change selon le lieu et au fil du temps.**

## Ce que tu peux dire — environ une minute

> Bonjour. Les satellites et les modèles scientifiques nous donnent beaucoup d'informations sur la Terre. Mais il est difficile de savoir quoi regarder, où regarder et si un changement dure vraiment dans le temps.
>
> Nous avons créé **Earth Trends Detective** pour rendre ces informations plus faciles à explorer. Dans l'application, on choisit une mesure — par exemple la température, la pluie ou la végétation — puis un lieu et une période. On voit le résultat sur une carte et sur un graphique. L'application indique aussi si la tendance observée est assez claire dans les données ou si elle reste incertaine.
>
> On peut ensuite comparer deux lieux. Par exemple, avec notre indicateur satellitaire de végétation, la tendance va dans un sens dans notre zone d'exemple en Amazonie et dans l'autre sens dans notre zone d'exemple au Sahara. Cela montre pourquoi il est utile de regarder les régions séparément.
>
> L'application aide à voir ce qui change et où. Elle ne prétend pas expliquer pourquoi le changement arrive. Elle donne au public un moyen simple de poser une question, de regarder les données et de mieux comprendre ce qu'elles montrent.

## Si tu as seulement 30 secondes

> **Earth Trends Detective transforme des mesures de la Terre en une enquête simple.** On choisit un indicateur, un lieu et une période. L'application affiche une carte, un graphique et des explications sur la tendance. On peut comparer deux lieux pour voir si la même mesure évolue de la même façon. C'est un outil pour explorer les données, pas pour inventer une cause.

## Quoi montrer dans l'application — environ 2 à 3 minutes

### 1. Accueil

Montre le titre et la carte d'aperçu. Dis simplement : **« La question de départ est : est-ce que la Terre change, et est-ce que ce changement est le même partout ? »**

### 2. Les mesures disponibles

Ouvre **Variables**. Explique que l'application permet actuellement d'étudier huit mesures NASA déjà prêtes :

- la température de surface ;
- les précipitations ;
- deux indicateurs de végétation ;
- l'évaporation ;
- l'humidité du sol ;
- la température de l'air en surface ;
- le dioxyde d'azote dans l'atmosphère.

Tu peux ajouter : **« Ces mesures viennent de différents satellites et modèles. Elles n'ont pas toutes la même période disponible ; l'application affiche les dates pour chaque mesure. »**

### 3. Une analyse dans Explorer

Ouvre **Explorer**, choisis l'indicateur de végétation MODIS appelé **NDVI**, puis garde le rectangle d'exemple de l'Amazonie et **Toute la série**.

Dis : **« Cette zone est un rectangle d'étude ; ce n'est pas une frontière exacte de l'Amazonie. Les données affichées ici vont de février 2000 à août 2011. »**

Montre ensuite :

- le rectangle d'étude dessiné sur la carte ;
- le fond de carte, qui sert à se repérer ;
- les couleurs de tendance : bleu pour une baisse de la mesure, rouge pour une hausse ;
- le graphique qui montre l'évolution mois par mois ;
- le résultat qui résume le rythme et le niveau de certitude.

Pour expliquer les points sur la carte : **« Ils signalent les zones où les données ne donnent pas une preuve assez forte d'une tendance, selon le contrôle statistique utilisé pour la carte. »**

### 4. Comparer deux lieux

Ouvre **Comparer** en gardant la même mesure, le NDVI. Choisis l'Amazonie et le Sahara.

Dis : **« Nous regardons le même indicateur dans deux zones. Dans la série locale de février 2000 à août 2011, la tendance estimée baisse dans le rectangle amazonien et monte dans le rectangle saharien. C'est un exemple de changement régional différent. L'application ne dit pas que l'un est la cause de l'autre. »**

Les valeurs vérifiées dans les données locales sont d'environ **−0,000625 par an** pour la zone amazonienne et **+0,000413 par an** pour la zone saharienne. Tu n'as pas besoin de prononcer ces chiffres : ils sont là si le jury demande le taux exact. L'indice est un signal lié à la végétation, pas une mesure directe de chaque plante.

### 5. Si le jury veut plus de détails

Ouvre **Méthodes** pour montrer comment l'application estime une tendance et vérifie si elle est convaincante. Ouvre **Ressources** uniquement si tu veux parler des outils externes et de CUAHSI.

## Expliquer les mots difficiles simplement

- **Indicateur :** une mesure qui nous renseigne sur un aspect de la Terre, par exemple la pluie ou l'humidité du sol.
- **Tendance :** la direction générale d'une mesure au fil des années : elle monte, baisse ou reste proche du même niveau.
- **Significative :** les données donnent assez d'éléments pour distinguer une tendance du bruit et des variations habituelles. Cela ne prouve pas que la tendance est vraie à 100 %, et cela n'en donne pas la cause.
- **Saisons :** des variations qui reviennent chaque année. L'application les sépare de l'évolution de long terme pour rendre la tendance plus facile à voir.
- **Rectangle d'étude :** la zone choisie sur la carte. Il peut inclure des endroits voisins ou de l'océan ; ce n'est pas une frontière administrative exacte.

## Questions probables

### « Est-ce que votre application explique la cause du changement ? »

Non. Elle montre la mesure qui change, le lieu, la direction, le rythme et le niveau de certitude. Trouver la cause demande une étude supplémentaire.

### « Une zone rouge est-elle forcément en meilleure santé ? »

Non. Rouge veut seulement dire que la mesure choisie augmente. Pour certaines mesures, une hausse peut être bonne ; pour d'autres, elle peut être inquiétante. Il faut connaître la variable pour interpréter le résultat.

### « Pourquoi les données s'arrêtent-elles à des dates différentes ? »

Chaque satellite ou modèle a sa propre période de données. Dans les données actuelles, GISTEMP va de janvier 1880 à septembre 2026 ; MODIS NDVI/EVI de février 2000 à août 2011 ; les précipitations GPM de janvier 2000 à septembre 2025. L'application affiche la couverture de chaque mesure et explique quand une période demandée n'est pas disponible.

### « Pourquoi comparer des rectangles plutôt que des pays ? »

Les rectangles permettent de choisir rapidement une zone et de dessiner sa propre emprise. Ils sont pratiques pour l'analyse, mais ne suivent pas exactement les frontières d'un pays ou d'un écosystème.

### « Est-ce que CUAHSI est la même chose que les données NASA de l'Explorer ? »

Non. CUAHSI donne accès à des mesures prises par des stations hydrologiques. Une station est un point précis. Les données NASA de l'Explorer sont analysées sur une zone. L'application garde ces deux parcours distincts pour ne pas les confondre.

### « Est-ce que les ressources comme Giovanni et NOAA sont intégrées directement ? »

CUAHSI dispose d'une recherche de stations directement dans l'application. Giovanni, AppEEARS, NASA Hydrology Time Series et NOAA CDO sont proposés comme outils externes ; leurs séries téléchargées peuvent être importées quand elles sont compatibles. Ne dis pas que ces portails sont automatisés de bout en bout.

## Points à garder en tête pendant la présentation

- Ne dis pas que l'application trouve les causes : elle montre des tendances, pas leurs mécanismes.
- Ne présente pas les rectangles comme des frontières exactes.
- Précise que les périodes varient selon les mesures.
- Le fond de carte sert à se repérer ; les résultats scientifiques viennent des données choisies.
- Si un résultat n'est pas significatif, explique qu'il reste intéressant mais que les données ne permettent pas encore de conclure clairement.
- La démonstration actuelle fonctionne en local ; ne la présente pas comme un site public déjà déployé.

## Conclusion à dire

> Avec Earth Trends Detective, on n'a pas besoin d'être spécialiste pour commencer à explorer les changements de la Terre. On choisit une mesure, on regarde un lieu, puis on examine les indices. L'application rend les données plus faciles à comprendre tout en montrant clairement ce qu'elles peuvent — et ne peuvent pas — nous apprendre.

## Pour préparer les réponses techniques

- [Méthodes et limites](METHODS.md).
- [Sources et produits de données](DATA_SOURCES.md).
- [État du projet et chiffres de validation](PROGRESS.md).
- [Notebook de validation GISTEMP](../notebooks/01_validation_gistemp.ipynb).
- [Cahier des charges du défi](../AGENT_BRIEF.md), en particulier la section 1 bis.
