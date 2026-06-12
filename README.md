# TER PICOPATT

Ce dépôt regroupe le travail réalisé dans le cadre du TER du projet ANR
PICOPATT, mené au LIRMM avec l'équipe ADVANSE et en collaboration avec
AAU/CRENAU.

Le projet étudie les picoclimats urbains de Montpellier à partir d'une station
météorologique mobile. Le travail porte principalement sur la température
moyenne radiante, notée `tmrt`, mesurée le long de trois parcours :
Antigone, Boulevards et Écusson.

## Résultat du projet

Le semestre 1 a été consacré au nettoyage, à la structuration et à l'analyse
exploratoire des mesures PICOPATT.

Le semestre 2 a permis de construire une chaîne de prédiction complète :

```text
mesures PICOPATT
        +
contexte météorologique Météo-France
        +
64 embeddings spatiaux AlphaEarth
        ↓
prédiction de la tmrt
        ↓
spatialisation sur une grille à 10 m
        ↓
heatmap et application web interactive
```

La grille finale contient `1 469 430` points et couvre environ `147 km²`
autour de Montpellier. La carte est une spatialisation exploratoire produite
pour un scénario météorologique fixé. Elle ne correspond pas à des mesures
réalisées partout dans la ville.

## Application

L'application permet de :

- visualiser la heatmap de `tmrt` prédite
- afficher les parcours PICOPATT
- comparer les valeurs prédites, observées et les erreurs sur les parcours
- filtrer la heatmap par plage de `tmrt`
- sélectionner une zone géographique
- exporter les coordonnées et les prédictions sélectionnées en CSV

Application en ligne :
[https://picocarte.alwaysdata.net](https://picocarte.alwaysdata.net)

Pour lancer l'application localement :

```powershell
cd app
python -m http.server 8765 --bind 127.0.0.1
```

Puis ouvrir [http://127.0.0.1:8765](http://127.0.0.1:8765).

## Enjeu méthodologique

Les mesures successives du chariot sont très proches dans le temps et dans
l'espace. Elles ne sont donc pas indépendantes et identiquement distribuées.
Un découpage aléatoire ligne par ligne peut placer des observations presque
identiques dans l'entraînement et dans le test, ce qui produit une évaluation
trop optimiste.

Le projet compare ainsi plusieurs protocoles :

- split aléatoire
- split spatial par parcours
- split spatio-temporel par blocs de parcours et de jours
- agrégations spatiales à 10 m et 20 m
- répétition des splits pour étudier leur robustesse

Les performances doivent toujours être lues avec le protocole d'évaluation
associé. Le modèle décrit mieux le centre de la distribution que les valeurs
extrêmes de `tmrt`.

## Arborescence

```text
TER-Picopatt/
├── analyse_exploratoire/   Notebooks du semestre 1
├── app/                    Génération et interface de la webapp
├── data/                   Données locales non versionnées
├── prediction/             Modélisation, évaluation et spatialisation
├── rapport/
│   ├── s1/                 Rapport du semestre 1
│   └── s2/                 Rapport final du semestre 2
├── src/picopatt/           Fonctions Python partagées
└── requirements.txt        Dépendances Python
```

Chaque dossier contient un README plus détaillé.

## Installation

Depuis la racine du dépôt :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Les notebooks peuvent ensuite être ouverts avec Jupyter ou directement dans
Visual Studio Code.

## Données

Les données volumineuses ne sont pas incluses dans Git. Les notebooks et
scripts utilisent principalement :

- `data/raw/` pour les données PICOPATT brutes
- `data/processed/picopatt/` pour les mesures nettoyées
- `data/processed/meteofrance/` pour les observations horaires
- `data/processed/alphaearth/` pour les embeddings et la grille à 10 m
- `data/processed/results/` pour les métriques des modèles
- `data/processed/prediction/` pour les prédictions et exports cartographiques

Voir [data/README.md](data/README.md) pour l'organisation détaillée.

## Rapports

- [Rapport du semestre 1](rapport/s1/Rapport_TER_PICOPATT.pdf)
- [Rapport du semestre 2](rapport/s2/Rapport_TER_PICOPATT_S2.pdf)

## Auteurs

Ayoub AKKOUH, Anthony COMBES-AGUÉRA, Youssef EL ALAOUI et Dylla Liesse IZERE.
