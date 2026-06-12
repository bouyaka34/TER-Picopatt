# Rapport du semestre 2

Ce dossier contient le rapport final du TER PICOPATT consacré à la prédiction
et à la spatialisation de la `tmrt`.

## Contenu

- `Rapport_TER_PICOPATT_S2.tex` : source LaTeX principale
- `Rapport_TER_PICOPATT_S2.pdf` : version compilée
- `references.bib` : bibliographie
- `Images/` : logos, figures de données, résultats de modèles, heatmaps et
  captures de l'application
- `out/` : sorties complémentaires de compilation

Le rapport présente chronologiquement :

1. le projet PICOPATT et le travail du semestre 1
2. les données PICOPATT, Météo-France et AlphaEarth
3. la première modélisation avec HistGradientBoosting
4. le problème des données non indépendantes
5. les splits spatiaux et spatio-temporels
6. les essais CatBoost et l'analyse des erreurs
7. la construction de la grille, de la heatmap et de la webapp
8. les limites et perspectives

## Compilation

Depuis la racine du dépôt :

```powershell
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=rapport\s2 rapport\s2\Rapport_TER_PICOPATT_S2.tex
biber rapport\s2\Rapport_TER_PICOPATT_S2
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=rapport\s2 rapport\s2\Rapport_TER_PICOPATT_S2.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=rapport\s2 rapport\s2\Rapport_TER_PICOPATT_S2.tex
```

Le PDF doit être fermé pendant la compilation, sinon MiKTeX peut afficher :

```text
I can't write on file `Rapport_TER_PICOPATT_S2.pdf'
```

Les passages successifs de `pdflatex` et `biber` sont nécessaires pour mettre
à jour la bibliographie, la table des matières et les renvois vers les figures
et tableaux.
