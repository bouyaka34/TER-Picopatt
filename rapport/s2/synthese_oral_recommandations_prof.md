# Synthese orale - recommandations professeur

## 1. Pourquoi faire un modele

- Les mesures PICOPATT par chariot sont precises, mais ponctuelles et couteuses.
- L'objectif n'est pas seulement de predire TMRT sur les points mesures.
- L'objectif est de preparer une densification spatiale a partir de variables disponibles sur l'espace, notamment AlphaEarth, la meteo generale et le contexte temporel.

## 2. Pourquoi les donnees ne sont pas IID

- Resultat observe: le jeu contient 341,281 lignes, mais seulement 73 passages track_id + date + M_slot.
- Les points consecutifs d'un passage sont proches dans le temps et dans l'espace.
- Plusieurs lignes appartiennent a une meme section ou a un meme passage.
- Interpretation: le nombre de lignes ne correspond pas au nombre de situations independantes.

## 3. Pourquoi le split aleatoire peut tromper

- Le split aleatoire est conserve comme baseline naive.
- Il peut placer dans train et test des points voisins, parfois issus du meme passage.
- Il peut donc donner une estimation optimiste de la generalisation.

## 4. Splits plus robustes testes

- Split par date: test de generalisation temporelle.
- Split par passage: groupe = track_id + date + M_slot.
- Split spatial: groupe = track_id + section_id quand disponible.
- Leave-one-track-out: entrainement sur deux parcours et test sur le troisieme.

## 5. Performances observees

- Modele principal: HistGradientBoosting avec le feature set generalisable.
- MAE split aleatoire naive: 1.716.
- MAE split par date: 4.326.
- MAE split par passage: 3.511.
- MAE split spatial par section: 2.306.
- MAE leave-one-track-out: 3.741.
- Resultat observe: les scores doivent etre lus split par split, pas seulement via le split aleatoire.
- Interpretation: les splits temporels et spatiaux sont plus proches de la question de generalisation.

## 6. Surprediction et biais

- Resultat observe: le biais moyen global prediction - observation est 1.146 degC sur l'analyse de residus.
- Formulation prudente: On observe une tendance a la surprediction dans certains cas, mais cette observation doit etre interpretee avec prudence car le jeu de test contient une forte autocorrelation spatiale et temporelle. Le nombre de lignes testees ne correspond pas necessairement au nombre de situations independantes.
- Les intervalles de confiance sont estimes par bootstrap de passages quand c'est possible.

## 7. Ce que montre la heatmap

- La carte produite correspond a: points PICOPATT disponibles.
- Les coordonnees lon/lat sont utilisees pour afficher les predictions, pas comme predicteurs du modele principal.
- Resultat observe: la figure donne une spatialisation des valeurs TMRT predites disponibles.

## 8. Limites actuelles

- Aucune donnee manquante n'a ete inventee.
- Les valeurs predicteurs physiquement impossibles sont masquees en NaN, puis imputees dans le pipeline a partir du train uniquement.
- Les flux radiatifs mesures par le chariot ne sont pas utilises dans le modele principal generalisable.
- Si aucune grille AlphaEarth externe n'est presente, la carte reste limitee aux points disponibles.
- La PCA AlphaEarth existante est reutilisee comme donnees deja produites; une variante stricte pourrait recalculer la PCA dans chaque fold.

## 9. Prochaines etapes

- Extraire AlphaEarth sur une vraie grille couvrant la zone d'interet.
- Definir des scenarios meteorologiques et solaires explicites pour chaque carte.
- Comparer plusieurs saisons ou campagnes si de nouvelles donnees arrivent.
- Renforcer les intervalles d'incertitude par bootstrap spatial/temporel par blocs.
