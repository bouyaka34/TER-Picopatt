# Données

Ce dossier sert à organiser les données en local. Son contenu n'est pas versionné dans Git, sauf ce README et les fichiers `.gitkeep`.

- `raw/` : données brutes PICOPATT, non modifiées.
- `processed/picopatt/clean_nozeros/` : fichiers PICOPATT nettoyés produits par `analyse_exploratoire/NoZero.ipynb`.
- `processed/alphaearth/alphaearth_data/` : grilles, points et tables AlphaEarth préparés par les notebooks AlphaEarth.
- `processed/prediction/` : exports utilisés par la prédiction TMRT, les heatmaps, les évaluations et l'application.
- `external/alphaearth/` : exports AlphaEarth externes ou téléchargés, dont les lots venant d'Earth Engine.

Les figures ne sont pas rangées dans `data/` : elles restent dans le dossier `figures/` du thème qui les génère.
