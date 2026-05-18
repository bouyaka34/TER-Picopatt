# TER-Picopatt

Ce dépôt regroupe le travail réalisé dans le cadre du TER autour du projet ANR PICOPATT, mené au LIRMM (équipe ADVANSE) en collaboration avec AAU/CRENAU.

L'objectif est d'analyser les séries temporelles produites par une station météorologique mobile sur plusieurs parcours urbains, puis de préparer la prédiction de la TMRT et la construction de silhouettes de picoclimats urbains.

## Arborescence

- `data/` : emplacement local des données. Les données brutes et traitées ne sont pas versionnées, sauf les fichiers de structure.
- `src/picopatt/` : fonctions Python communes réutilisables par les notebooks et scripts.
- `analyse_exploratoire/` : notebooks de prise en main, nettoyage, contrôle qualité et analyse exploratoire.
- `analyse_exploratoire/figures/` : figures exportées pour l'analyse exploratoire.
- `prediction/` : notebooks et scripts pour la prédiction de la TMRT et la heatmap de Montpellier.
- `prediction/figures/` : figures d'évaluation et de diagnostic des modèles.
- `app/` : application web de visualisation de la heatmap TMRT.
- `rapport/s1/` : rapport et ressources du semestre 1.
- `rapport/s2/` : notes et ressources du semestre 2.

## Données

Les données brutes PICOPATT, les exports AlphaEarth, les fichiers Météo-France et les résultats volumineux ne sont pas inclus directement dans le dépôt.

Les notebooks sont prévus pour lire les données depuis `data/` en local. Les dossiers `data/raw/`, `data/processed/` et `data/external/` servent de points d'entrée, mais leur contenu est ignoré par Git.

## Contenu scientifique

- contrôle de couverture et de complétude par parcours et par créneau
- nettoyage des mesures et gestion des valeurs aberrantes
- traitement des zéros assimilés à des défauts capteurs
- distributions, corrélations et profils spatio-temporels
- préparation des variables AlphaEarth et Météo-France
- prédiction de la TMRT et visualisation cartographique

## Auteurs

Ayoub AKKOUH, Anthony COMBES-AGUÉRA, Youssef EL ALAOUI, Dylla Liesse IZERE.
