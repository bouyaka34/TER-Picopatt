# TER-Picopatt

Travail réalisé dans le cadre du TER autour du projet ANR **PICOPATT** (Patterns picoclimatiques urbains), mené au LIRMM (équipe ADVANSE) en collaboration avec AAU/CRENAU.

Objectif : analyser les séries temporelles produites par une station météorologique mobile (mesures le long de parcours urbains), puis progresser vers la construction de **silhouettes** décrivant des picoclimats urbains.

## Organisation du dépôt (par branches)

Ce dépôt est volontairement réparti en plusieurs branches :

- `main` : rapport en LaTeX 
- `Notebook` : notebooks pour l’analyse exploratoire
- `Figures` : figures exportées depuis les notebooks
- `test` : essais, versions de travail, prototypage

## Contexte des données (résumé)

Les premières analyses portent sur les campagnes de Montpellier (octobre 2024 à mi-janvier 2025), sur trois parcours : Antigone, Boulevards, Écusson.  
Chaque journée comprend jusqu’à 4 créneaux (`M1` à `M4`) espacés de 3 heures.

## Contenu scientifique (résumé)

- contrôle de couverture et complétude (par parcours et créneau)
- nettoyage et gestion des valeurs aberrantes
- gestion des zéros assimilés à des défauts capteurs (imputation courte, sinon NaN)
- analyses exploratoires : distributions, corrélations, profils spatio-temporels
- préparation des étapes suivantes : silhouettes et pistes de deep learning

## Données

Les données brutes PICOPATT (CSV) ne sont pas incluses dans ce dépôt.  
Les notebooks sont conçus pour fonctionner en pointant vers un dossier de données local.

## Auteurs

Ayoub AKKOUH, Anthony COMBES-AGUÉRA, Youssef EL ALAOUI, Dylla Liesse IZERE.
