# Analyse exploratoire

Ce dossier regroupe les notebooks du semestre 1 consacrés à la préparation et
à la compréhension des mesures PICOPATT.

## Notebooks

- `Analyse_exploratoire.ipynb` : distributions, corrélations, profils par
  parcours et comparaisons selon les créneaux `M_slot`.
- `NoZero.ipynb` : traitement des zéros assimilés à des défauts de capteurs,
  imputation des séquences courtes et export des fichiers nettoyés vers
  `data/processed/picopatt/clean_nozeros/`.
- `Localisation.ipynb` : contrôle des coordonnées, visualisation des parcours
  et premières fonctionnalités de sélection cartographique.
- `Clustering.ipynb` : essais de regroupement de profils et comparaison de
  passages.
- `agreg.ipynb` : agrégations par passage, parcours ou créneau.

## Sorties

Les figures sont enregistrées dans `analyse_exploratoire/figures/`. Les
données nettoyées et les tables intermédiaires sont enregistrées dans
`data/processed/`.

Les travaux de ce dossier préparent la modélisation du semestre 2 en
fournissant une cible `tmrt` contrôlée, des identifiants de parcours cohérents
et une première compréhension des dépendances spatiales et temporelles.
