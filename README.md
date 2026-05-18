# TER-Picopatt

Ce depot regroupe le travail realise dans le cadre du TER autour du projet ANR PICOPATT, mene au LIRMM (equipe ADVANSE) en collaboration avec AAU/CRENAU.

L'objectif est d'analyser les series temporelles produites par une station meteorologique mobile sur plusieurs parcours urbains, puis de preparer la prediction de la TMRT et la construction de silhouettes de picoclimats urbains.

## Arborescence

- `data/` : emplacement local des donnees. Les donnees brutes et traitees ne sont pas versionnees, sauf les fichiers de structure.
- `src/picopatt/` : fonctions Python communes reutilisables par les notebooks et scripts.
- `analyse_exploratoire/` : notebooks de prise en main, nettoyage, controle qualite et analyse exploratoire.
- `analyse_exploratoire/figures/` : figures exportees pour l'analyse exploratoire.
- `prediction/` : notebooks et scripts pour la prediction de la TMRT et la heatmap de Montpellier.
- `prediction/figures/` : figures d'evaluation et de diagnostic des modeles.
- `app/` : application web de visualisation de la heatmap TMRT.
- `rapport/s1/` : rapport et ressources du semestre 1.
- `rapport/s2/` : notes et ressources du semestre 2.

## Donnees

Les donnees brutes PICOPATT, les exports AlphaEarth, les fichiers Meteo-France et les resultats volumineux ne sont pas inclus directement dans le depot.

Les notebooks sont prevus pour lire les donnees depuis `data/` en local. Les dossiers `data/raw/`, `data/processed/` et `data/external/` servent de points d'entree, mais leur contenu est ignore par Git.

## Contenu scientifique

- controle de couverture et de completude par parcours et par creneau
- nettoyage des mesures et gestion des valeurs aberrantes
- traitement des zeros assimiles a des defauts capteurs
- distributions, correlations et profils spatio-temporels
- preparation des variables AlphaEarth et Meteo-France
- prediction de la TMRT et visualisation cartographique

## Auteurs

Ayoub AKKOUH, Anthony COMBES-AGUERA, Youssef EL ALAOUI, Dylla Liesse IZERE.
