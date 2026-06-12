# Prédiction et spatialisation de la tmrt

Ce dossier contient les notebooks et scripts du semestre 2. L'objectif est de
prédire la `tmrt` mesurée par PICOPATT à partir de variables utilisables en
dehors des parcours :

- les observations horaires de Météo-France pour le contexte météorologique
- les 64 embeddings AlphaEarth `A00` à `A63` pour le contexte spatial

Les coordonnées servent aux jointures et à la cartographie, mais elles ne sont
pas utilisées comme variables explicatives dans le modèle final de la heatmap.

## Fichiers principaux

- `Alphaearth.ipynb` : association des embeddings AlphaEarth aux points
  PICOPATT et préparation des tables spatiales.
- `Grille_AE_mtp.ipynb` : construction de la grille régulière de Montpellier
  et préparation des extractions AlphaEarth.
- `Prediction.ipynb` : notebook principal de préparation des variables,
  entraînement, comparaison des modèles, évaluation et analyse des erreurs.
- `Prediction_colab_version.ipynb` : version prévue pour une exécution sur
  Google Colab.
- `Prediction_visualisation.ipynb` : génération de figures à partir des CSV
  présents dans `data/processed/results/` et
  `data/processed/prediction/`.
- `heatmap_montpellier_10m.py` : réentraînement du modèle choisi, prédiction
  sur la grille à 10 m et génération des sorties cartographiques.

## Évolution de la modélisation

Le travail a suivi plusieurs étapes :

1. première régression avec `HistGradientBoostingRegressor`
2. comparaison de Météo-France seul, Météo-France avec les 64 embeddings
   AlphaEarth et Météo-France avec une ACP des embeddings
3. enrichissement des variables météorologiques et temporelles
4. remplacement du split aléatoire par des évaluations spatiales puis
   spatio-temporelles
5. répétition des splits pour mesurer la sensibilité aux blocs choisis
6. test de `CatBoostRegressor` et d'un grid search léger
7. analyse des erreurs par parcours, créneau, niveau de `tmrt` et météo
8. agrégations spatiales à 10 m et 20 m pour réduire la redondance locale

L'ACP ne donne pas d'amélioration nette par rapport aux 64 embeddings bruts.
Le split aléatoire reste très favorable, car il mélange des observations très
proches entre l'entraînement et le test.

## Résultats d'évaluation

Les résultats ne doivent pas être comparés sans tenir compte du protocole, du
modèle et du niveau d'agrégation.

Pour le split spatial fixe sauvegardé dans
`data/processed/results/tmrt_spatial_split_metrics.csv`, le test sur Antigone
donne :

| MAE | RMSE | R² |
|---:|---:|---:|
| 5,16 °C | 7,54 °C | 0,439 |

Pour le split spatio-temporel fixe sauvegardé dans
`data/processed/results/tmrt_spatiotemporal_split_metrics.csv`, le test donne :

| MAE | RMSE | R² |
|---:|---:|---:|
| 3,77 °C | 5,82 °C | 0,493 |

Les répétitions de split sont disponibles dans
`tmrt_spatiotemporal_repeated_split_results.csv` et leur synthèse dans
`tmrt_spatiotemporal_repeated_summary.csv`.

L'expérience non-i.i.d. et les agrégations spatiales sont exportées dans
`data/processed/prediction/tmrt_pred_report/` :

- `tmrt_catboost_non_iid_aggregation_ww_eval.csv`

Ces expériences montrent que le score du split aléatoire ne représente pas la
capacité du modèle à généraliser à des jours ou parcours non vus.

## Variables Météo-France

Le modèle de spatialisation utilise 38 variables météorologiques brutes ou
dérivées, parmi lesquelles :

- température et humidité : `T`, `TD`, `TN`, `TX`, `U`, `UN`, `UX`, `UABS`
- pression : `PSTAT`, `PMER`
- vent et rafales : `FF`, `FXY`, `FXI`, `DD`, `DXI`
- pluie : `RR1`, `DRR1`
- nébulosité et visibilité : `N`, `NBAS`, `WW`, `VV`
- rayonnement et insolation : `INS`, `GLO`, `GLO2`

Les directions sont encodées avec des composantes sinus et cosinus. Le jeu
contient également des variables dérivées comme `wind_u`, `wind_v`,
`dewpoint_depression`, `rain_flag`, `GLO_x_INS`, `FF_x_GLO`, `N_x_GLO` et
`T_x_GLO`.

`WW` a été testé comme variable catégorielle CatBoost. Cette représentation
n'améliore pas clairement les splits groupés. La spatialisation actuelle
utilise donc sa représentation numérique et des indicateurs dérivés.

## Analyse des erreurs

Les exports d'analyse se trouvent dans
`data/processed/prediction/error_analysis/` et les figures associées dans
`prediction/figures/model_analysis/`.

Les diagnostics montrent notamment :

- des performances différentes selon les parcours et les créneaux
- une difficulté plus forte sur l'Écusson dans l'évaluation analysée
- une augmentation de l'erreur lorsque le rayonnement global est fort
- un lissage des fortes valeurs de `tmrt`

La carte finale doit donc être interprétée comme une spatialisation
exploratoire, et non comme une mesure directe ou une estimation d'incertitude
faible.

## Génération de la heatmap

Le script utilise par défaut `CatBoostRegressor` et prédit la grille par blocs
de 50 000 lignes :

```powershell
python prediction\heatmap_montpellier_10m.py
```

Pour régénérer uniquement les figures à partir des prédictions existantes :

```powershell
python prediction\heatmap_montpellier_10m.py --plot-existing data\processed\prediction\heatmap_tmrt_montpellier_10m\tmrt_montpellier_10m_predictions_catboost.csv
```

Le modèle HistGradientBoosting reste disponible :

```powershell
python prediction\heatmap_montpellier_10m.py --model histgbr
```

Les principales sorties sont écrites dans :

- `data/processed/prediction/heatmap_tmrt_montpellier_10m/`
- `prediction/figures/heatmap_tmrt_montpellier_10m/`

La sortie CatBoost actuelle contient `1 469 430` prédictions sur une grille à
10 m. Le raster associé contient `1314 × 1133` cellules.

## Scénario de la carte

La carte publiée utilise les valeurs médianes du jeu d'entraînement pour les
variables qui ne viennent pas d'AlphaEarth. Les principales valeurs sont :

| Variable | Valeur |
|---|---:|
| `T` | 12,0 °C |
| `U` | 65 % |
| `FF` | 3,6 m/s |
| `RR1` | 0 mm |
| `GLO` | 54 W/m² |
| `INS` | 15 min |
| `WW` | 0 |

La météo étant identique sur toute la grille, les contrastes affichés viennent
principalement de la description spatiale AlphaEarth.
