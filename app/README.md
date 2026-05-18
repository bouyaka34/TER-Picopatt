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

Il lit les données rangées dans `data/processed/prediction/` et l'image de heatmap sélectionnée dans `prediction/figures/heatmap_tmrt_montpellier_10m/`. S'ils ont été supprimés, il faut les régénérer avec :

```powershell
python app\build_tmrt_webapp.py
```

Puis lancer l'application :

```powershell
cd app
python -m http.server 8765 --bind 127.0.0.1
```

Puis ouvrir :

```text
http://127.0.0.1:8765/webapp_tmrt_montpellier/
```
