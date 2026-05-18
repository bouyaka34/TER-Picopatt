# Application

Application web de visualisation de la heatmap TMRT.

## Fichiers

- `build_tmrt_webapp.py` : prépare les données JavaScript et les tuiles nécessaires à l'application.
- `webapp_tmrt_montpellier/` : interface HTML, CSS et JavaScript.

## Sorties générées

Le script écrit les fichiers générés dans `app/webapp_tmrt_montpellier/` :

- `scenario-data.js`
- `heatmap_tiles/`
- `heatmap_value_tiles/`

Il lit les données rangées dans `data/processed/prediction/` et l'image de heatmap sélectionnée dans `prediction/figures/heatmap_tmrt_montpellier_10m/`.
