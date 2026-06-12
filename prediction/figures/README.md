# Figures de prédiction

Ce dossier contient les figures générées par les notebooks et scripts du
dossier `prediction/`.

## Organisation

- `prediction_data/` : distributions de `tmrt` et description des données
  d'entrée.
- `eval/` : prédictions contre observations, résidus et comparaisons de splits.
- `no_iid/` : autocorrélation et structure des groupes spatio-temporels.
- `model_analysis/` : importance des variables, erreurs par groupe, par niveau
  de `tmrt` et selon les conditions météorologiques.
- `tmrt_pred/` : comparaisons historiques des jeux de variables et modèles.
- `heatmap_tmrt_montpellier_10m/` : heatmap statique, overlay transparent et
  première carte HTML.
- `report_extra/` : figures supplémentaires préparées pour le rapport S2.
- `biais/` : anciens diagnostics de biais conservés pour la traçabilité.

Les tables qui servent à produire ces figures sont stockées dans
`data/processed/results/` et `data/processed/prediction/`.

La majorité des figures de synthèse peut être régénérée avec
`Prediction_visualisation.ipynb`.
