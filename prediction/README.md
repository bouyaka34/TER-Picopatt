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
- Les figures issues de l'entraînement principal sont réparties entre `figures/prediction_data/`, `figures/eval/` et `figures/model_analysis/`.
- `figures/heatmap_tmrt_montpellier_10m/` : cartes TMRT produites sur la grille AlphaEarth à 10 m.

La figure `predicted_vs_observed_by_split.png` utilise les prédictions détaillées par split si `data/processed/prediction/eval/predictions_by_split.csv` existe. Sinon, le notebook indique la limite et utilise les prédictions disponibles dans `tmrt_pred_report`.

## Variables Météo-France du CatBoost

Le modèle CatBoost utilisé pour la heatmap 10 m reprend désormais un jeu de variables Météo-France plus physique :

- température et humidité : `T`, `TD`, `TN`, `TX`, `U`, `UN`, `UX`, `UABS`
- pression : `PSTAT`, `PMER`
- vent et rafales : `FF`, `FXY`, `FXI`, avec `DD` et `DXI` encodées en sinus/cosinus
- pluie : `RR1`, `DRR1`
- nébulosité et visibilité : `N`, `NBAS`, `WW`, `VV`
- rayonnement : `INS`, `GLO`, `GLO2`

Les colonnes qualité `Q...` ne sont plus utilisées comme variables météo. Le modèle ajoute des variables dérivées : composantes circulaires du vent, `wind_u`, `wind_v`, `gust_u`, `gust_v`, `dewpoint_depression`, `T_range_hour`, `U_range_hour`, `rain_flag`, `rain_duration_weighted`, `GLO_x_INS`, puis les interactions temporelles/solaires déjà utilisées (`apparent_T`, `T_x_elev`, `FF_x_GLO`, `N_x_elev`, `GLO_x_elev`, `N_x_GLO`, `T_x_GLO`).

Une comparaison CatBoost sur split par blocs jour/parcours est exportée dans `data/processed/prediction/tmrt_pred_report/tmrt_catboost_mf_feature_set_comparison.csv`. Sur le test, le jeu enrichi passe de RMSE 5,981 à 5,889 °C, de MAE 3,796 à 3,714 °C et de R² 0,464 à 0,481 par rapport à l'ancien set météo.

## Évaluation non-IID et agrégation spatiale

La fin de `Prediction.ipynb` contient une expérience dédiée à l'autocorrélation : points bruts, agrégation par tronçons de 10 m et agrégation par tronçons de 20 m sont comparés avec trois splits (`random_row`, `passage_group`, `day_track_group`). Les résultats sont exportés dans `data/processed/prediction/tmrt_pred_report/tmrt_catboost_non_iid_aggregation_ww_eval.csv`.

Le split aléatoire reste très optimiste : sur les points bruts, le RMSE test est proche de 3,13 °C, alors qu'il monte à environ 5,10 °C en split par passage et 7,47 °C en split par bloc parcours+jour. L'agrégation réduit fortement la redondance des données : 341 281 points deviennent 22 185 lignes à 10 m et 11 224 lignes à 20 m. Sur les métriques point par point avec split groupé, l'agrégation à 20 m aide légèrement, mais les métriques moyennées par passage ne s'améliorent pas systématiquement.

`WW` a aussi été testé comme variable catégorielle CatBoost. Le gain est très faible sur split aléatoire et il n'améliore pas les splits robustes ; le modèle final conserve donc une représentation numérique enrichie par des flags météo (`ww_precip_flag`, `ww_fog_flag`, `ww_thunder_flag`).

## Analyse des erreurs

La fin de `Prediction.ipynb` contient aussi une analyse détaillée des erreurs du CatBoost sur un test robuste par blocs `track_id + jour`. Les tableaux sont exportés dans `data/processed/prediction/error_analysis/` et les figures dans `prediction/figures/model_analysis/`.

Sur ce test, le modèle obtient RMSE 5,93 °C, MAE 3,69 °C et un biais moyen `pred - obs` de -1,08 °C. Les erreurs ne sont pas homogènes : l'Écusson est le parcours le plus difficile (RMSE 6,51 °C, biais -2,31 °C), M2 est le créneau le plus difficile (RMSE 7,70 °C), et les pires combinaisons sont surtout `ecusson/M2`, `boulevards/M2`, `antigone/M3` et `ecusson/M3`.

Le diagnostic le plus important est la sous-prédiction des fortes TMRT : sur le quintile le plus chaud, le biais atteint -7,77 °C et la RMSE 11,30 °C. L'erreur augmente aussi quand le rayonnement global est fort ou très fort. Cela suggère que le modèle lisse trop les extrêmes : il décrit correctement le centre de la distribution, mais il manque encore les pics de TMRT, surtout en conditions très ensoleillées et dans certains environnements urbains.

Les profils `environment_proxy` sont des clusters AlphaEarth ordonnés par TMRT observée sous soleil. Ils donnent un proxy ombragé/dense vs ouvert/exposé, mais ne doivent pas être présentés comme une vérité terrain urbaine sans validation visuelle.
