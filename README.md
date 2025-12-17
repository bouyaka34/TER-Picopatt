# TER-Picopatt – branche `Figures`

Cette branche regroupe les figures exportées depuis les notebooks (branche `Notebook`) et utilisées dans le rapport.  
L’objectif est d’avoir un historique propre des sorties graphiques sans mélanger le code et les images.

## Contenu

On retrouve principalement :

- figures de complétude et couverture (passages distincts, densité d’échantillons, présence par date et par créneau)
- figures de nettoyage et contrôle qualité (boxplots avant/après correction, diagnostics d’anomalies, taux de NaN, taux de zéros)
- figures d’analyse exploratoire (distributions, boxplots/violinplots, corrélations, profils moyens par `M_slot`)
- profils à l’échelle d’un passage (comparaisons intra-journée, comparaisons multi-dates)

## Convention

Les fichiers sont nommés pour indiquer clairement :
- la variable (ex : `lw_down`, `pet`, `tmrt`, `ws`)
- le type de figure (ex : `dist`, `boxplot`, `corr`, `profil`, `compare`)
- le niveau de comparaison (parcours, `M_slot`, section, date)

## Lien avec les autres branches

- les figures sont produites par les notebooks de la branche `Notebook`
- elles sont ensuite intégrées dans le rapport LaTeX (branche `main`)

## Auteurs

Ayoub AKKOUH, Anthony COMBES-AGUÉRA, Youssef EL ALAOUI, Dylla Liesse IZERE.
