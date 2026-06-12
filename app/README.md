# Application cartographique PICOPATT

Ce dossier contient l'application statique utilisée pour explorer la
spatialisation de la `tmrt` prédite sur Montpellier.

Application publiée :
[https://picocarte.alwaysdata.net](https://picocarte.alwaysdata.net)

## Fonctionnalités

- fond satellite Esri avec repli OpenStreetMap
- heatmap de `tmrt` prédite sur une grille à 10 m
- réglage de l'opacité de la heatmap
- filtrage des valeurs visibles avec une plage de `tmrt`
- affichage des trois parcours PICOPATT
- modes tracé, valeur prédite, valeur observée et erreur
- sélection d'une zone dessinée ou de la vue actuelle
- combinaison de la zone géographique et du filtre de `tmrt`
- export CSV des coordonnées et valeurs sélectionnées

La heatmap correspond à un scénario météorologique fixé. Elle représente une
sortie de modèle, pas une campagne de mesure couvrant toute la ville.

## Organisation

- `build_tmrt_webapp.py` prépare les données et les couches nécessaires.
- `index.html` redirige la racine locale vers l'application.
- `webapp_tmrt_montpellier/index.html` contient la structure de l'interface.
- `webapp_tmrt_montpellier/styles.css` contient la mise en forme.
- `webapp_tmrt_montpellier/app.js` contient la logique Leaflet, les filtres et
  les sélections.
- `webapp_tmrt_montpellier/scenario-data.js` contient les métadonnées, les
  statistiques et les parcours simplifiés.
- `webapp_tmrt_montpellier/vendor/leaflet/` contient Leaflet localement afin
  d'éviter une dépendance au CDN.
- `webapp_tmrt_montpellier/heatmap_tiles/` contient les tuiles visuelles WebP.
- `webapp_tmrt_montpellier/heatmap_value_tiles/` contient les tuiles de valeurs
  utilisées par le filtre de `tmrt`.
- `webapp_tmrt_montpellier/selection_grid/` contient la grille binaire
  `float32` utilisée pour les sélections et les exports.

## Régénération

Le script attend notamment :

- les métadonnées et prédictions dans
  `data/processed/prediction/heatmap_tmrt_montpellier_10m/`
- les prédictions des parcours dans
  `data/processed/prediction/tmrt_predictions_grid_or_points.csv`
- les mesures nettoyées dans
  `data/processed/picopatt/clean_nozeros/`
- l'overlay de heatmap dans
  `prediction/figures/heatmap_tmrt_montpellier_10m/`

Depuis la racine du dépôt :

```powershell
python app\build_tmrt_webapp.py
```

Le script génère ou actualise :

- `scenario-data.js`
- `heatmap_overlay.png`
- les tuiles de zoom 12 à 17
- la grille binaire de sélection
- les données simplifiées des parcours

La génération des tuiles peut prendre du temps. Si les manifestes et les
fichiers sources n'ont pas changé, les couches existantes sont conservées.

## Lancement local

Depuis la racine du dépôt :

```powershell
cd app
python -m http.server 8765 --bind 127.0.0.1
```

Puis ouvrir :

[http://127.0.0.1:8765](http://127.0.0.1:8765)

Il ne faut pas ouvrir directement le fichier HTML avec `file://`, car le
navigateur doit charger les tuiles et la grille binaire par HTTP.

## Déploiement

L'application ne nécessite ni Flask, ni Node.js, ni base de données. Le contenu
de `app/webapp_tmrt_montpellier/` peut être publié comme site statique.

Pour AlwaysData :

```text
Type : Fichiers statiques
Répertoire racine : /home/picocarte/www/webapp_tmrt_montpellier/
```

Le fichier `index.html` doit se trouver directement dans ce répertoire.
