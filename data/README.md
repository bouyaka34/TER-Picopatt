# Organisation des données

Ce dossier centralise les données utilisées par les notebooks, les scripts de
prédiction et l'application. Les fichiers volumineux sont ignorés par Git.

## Structure

```text
data/
├── raw/
│   └── données PICOPATT brutes
├── external/
│   └── exports externes, notamment AlphaEarth
└── processed/
    ├── picopatt/
    ├── meteofrance/
    ├── alphaearth/
    ├── prediction/
    └── results/
```

## Données PICOPATT

- `processed/picopatt/clean_nozeros/` contient les fichiers nettoyés issus de
  `analyse_exploratoire/NoZero.ipynb`.
- Les fichiers conservent les mesures du chariot, les coordonnées, les
  identifiants de parcours et de sections, ainsi que la cible `tmrt`.

## Données Météo-France

- `processed/meteofrance/` contient les observations horaires utilisées pour
  reconstruire un contexte météorologique disponible en dehors des parcours.
- Les variables exploitées couvrent notamment la température, l'humidité, la
  pression, le vent, les précipitations, la nébulosité, la visibilité et le
  rayonnement.

## Données AlphaEarth

- `external/alphaearth/` peut recevoir les exports provenant de Google Earth
  Engine.
- `processed/alphaearth/alphaearth_data/picopatt_points.csv` contient les
  coordonnées PICOPATT préparées pour l'extraction.
- `processed/alphaearth/alphaearth_data/alphaearth_A00_A63_points.csv` contient
  les 64 embeddings associés aux points mesurés.
- `processed/alphaearth/alphaearth_data/mtp_grid_10m_points.csv` décrit la
  grille régulière à 10 m.
- `processed/alphaearth/alphaearth_data/mtp_points.csv` contient les embeddings
  AlphaEarth associés à cette grille et sert à la spatialisation.

## Prédictions et évaluations

- `processed/results/` contient les métriques, prédictions de test et résultats
  de grid search produits par `Prediction.ipynb`.
- `processed/prediction/tmrt_pred_report/` contient les comparaisons de jeux de
  variables, les expériences non-i.i.d. et les agrégations 10 m et 20 m.
- `processed/prediction/error_analysis/` contient les analyses d'erreurs par
  parcours, créneau, niveau de `tmrt` et conditions météorologiques.
- `processed/prediction/heatmap_tmrt_montpellier_10m/` contient les prédictions
  sur la grille et les métadonnées de la heatmap.
- `processed/prediction/tmrt_predictions_grid_or_points.csv` contient les
  prédictions utilisées pour afficher les parcours dans l'application.

## Figures

Les figures ne sont pas stockées dans `data/` :

- `analyse_exploratoire/figures/` pour le semestre 1
- `prediction/figures/` pour la modélisation et la spatialisation
- `rapport/s1/Images/` et `rapport/s2/Images/` pour les rapports

## Reproduction

Les données brutes, les exports Météo-France et les embeddings AlphaEarth ne
sont pas fournis directement dans Git. Pour reproduire toute la chaîne, il faut
reconstituer cette arborescence avant d'exécuter les notebooks.
