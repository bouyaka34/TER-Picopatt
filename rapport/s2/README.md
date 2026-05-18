# Rapport S2

Ce dossier est prévu pour le rapport du semestre 2.

Les figures du semestre 2 sont générées par les notebooks et scripts des dossiers `prediction/` et `app/`. Elles seront rangées ici seulement si elles sont directement intégrées au rapport.

## Origine des figures S2

- `prediction/Prediction.ipynb` génère les figures d'évaluation et d'analyse d'erreurs dans `prediction/figures/tmrt_pred/`.
- `prediction/Prediction_visualisation.ipynb` génère les figures d'analyse des données, des performances, des biais et des résidus dans `prediction/figures/`.
- `prediction/heatmap_montpellier_10m.py` génère les cartes Tmrt à 10 m dans `prediction/figures/heatmap_tmrt_montpellier_10m/`.
- `app/build_tmrt_webapp.py` utilise ces cartes pour générer les fichiers de l'application (`scenario-data.js`, tuiles de heatmap et tuiles de valeurs).
- `prediction/Alphaearth.ipynb` génère les figures de contrôle AlphaEarth dans `prediction/figures/alphaearth/`.
- `prediction/Grille_AE_mtp.ipynb` prépare la grille et les exports AlphaEarth ; il ne génère pas de figure principale.

La note `synthese_oral_recommandations_prof.md` vient des sorties de préparation orale et est rangée ici avec les éléments du S2.

Les figures `biais`, `eval`, `model_analysis`, `prediction_data` et `no_iid` sont régénérées par le notebook de visualisation.
