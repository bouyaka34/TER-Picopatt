# Utilitaires Python `picopatt`

Ce dossier regroupe les fonctions communes utilisées par les notebooks et les
scripts.

## Modules disponibles

- `io.py` : lecture des fichiers, chargement de plusieurs tables et création
  de dossiers.
- `cleaning.py` : normalisation des noms de parcours, extraction des
  informations depuis les noms de fichiers, conversion des dates et attribution
  des créneaux `M_slot`.
- `features.py` : statistiques descriptives et moyenne circulaire pour les
  directions.
- `__init__.py` : expose les fonctions principales du package.

## Modules réservés

- `alphaearth.py`
- `modeling.py`
- `mapping.py`

Ces trois modules sont encore vides ou minimaux. Les traitements AlphaEarth,
la modélisation et la cartographie restent principalement implémentés dans les
notebooks et scripts des dossiers `prediction/` et `app/`.

Pour utiliser le package depuis la racine du dépôt, le dossier `src/` doit être
présent dans le chemin Python.
