# TER-Picopatt – branche `Notebook`

Cette branche contient les notebooks Jupyter et le code Python utilisés pour l’analyse exploratoire des données PICOPATT (Montpellier) et la préparation des étapes suivantes autour des silhouettes de picoclimats.

## Contenu de la branche

- `Analyse_exploratoire.ipynb` : notebook principal (distributions, corrélations, profils, comparaisons par parcours et créneaux).
- `Localisation.ipynb` : éléments liés à la structuration spatiale et à la localisation (selon la version).
- `NoZero.ipynb` : traitement des zéros assimilés à des défauts capteurs (imputation courte puis NaN).
- `agreg.ipynb` : agrégations et tests (par parcours, créneau, etc.).
- `functions.py` : fonctions utilitaires communes.
- `requirements.txt` : liste de dépendances.

## Données

Les données brutes PICOPATT (CSV) ne sont pas incluses dans le dépôt.

Les notebooks supposent un dossier de données en local. Il faut donc adapter le chemin de chargement dans les premières cellules (variable du type `DATA_DIR` ou `path`).

## Sorties

Les notebooks génèrent des figures et sorties intermédiaires. Les figures finales sont destinées à être versionnées dans la branche `Figures` (ou exportées localement selon l’organisation choisie).

## Auteurs

Ayoub AKKOUH, Anthony COMBES-AGUÉRA, Youssef EL ALAOUI, Dylla Liesse IZERE.
