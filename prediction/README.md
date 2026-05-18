# Prédiction TMRT

Modélisation de la TMRT à partir des données PICOPATT, des variables Météo-France et des embeddings AlphaEarth.

## Fichiers

- `Prediction.ipynb` : entraînement, comparaison des modèles, analyse des erreurs et exports de prédiction.
- `Prediction_visualisation.ipynb` : notebook autonome pour générer les figures utiles à la présentation et à l'analyse de la prédiction.
- `heatmap_montpellier_10m.py` : prédiction de la TMRT sur la grille de Montpellier et génération des cartes.

## Figures générées

- `figures/prediction_data/` : aperçu des données utilisées pour la prédiction, distribution de la TMRT et différences selon les parcours et créneaux.
- `figures/eval/` : comparaison des stratégies de validation, prédiction vs observation et résidus par parcours/créneau.
- `figures/biais/` : biais moyen global et biais par groupe.
- `figures/model_analysis/` : analyse des erreurs du modèle, zones où les résidus sont forts et groupes les plus difficiles.
- `figures/no_iid/` : structure en blocs spatio-temporels et autocorrélation de la TMRT.
- `figures/tmrt_pred/` : figures issues de l'entraînement principal et de l'analyse d'erreurs.
- `figures/heatmap_tmrt_montpellier_10m/` : cartes TMRT produites sur la grille AlphaEarth à 10 m.

La figure `predicted_vs_observed_by_split.png` utilise les prédictions détaillées par split si `data/processed/prediction/eval/predictions_by_split.csv` existe. Sinon, le notebook indique la limite et utilise les prédictions disponibles dans `tmrt_pred_report`.
