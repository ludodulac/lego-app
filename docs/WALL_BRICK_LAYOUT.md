# WallBrickLayout v0.1

BH-005 introduit le premier placement déterministe de briques.

## Périmètre

Entrée : un mur rectangulaire exprimé directement en grille de briques :

- `width_studs` : largeur horizontale en tenons ;
- `height_bricks` : hauteur en briques standards ;
- épaisseur fixe : 1 tenon pour v0.1.

Sortie : une liste ordonnée de placements de briques canoniques sans trou ni chevauchement.

Cette version ne traite pas encore les ouvertures, les angles, les joints décalés, la stabilité structurelle, les couleurs ni la conversion mètres -> grille.

## Coordonnées locales

- X : horizontal, de gauche à droite ;
- Y : épaisseur du mur, fixée à 0 pour la face de référence ;
- Z : vertical, exprimé en couches de plate.

Une brique standard mesure 3 couches de plate en hauteur.

## Stratégie v0.1

Chaque rangée est remplie de gauche à droite avec la plus grande brique de largeur 1 disponible qui tient dans l'espace restant.

Ordre canonique utilisé :

1. `BRICK_1X8`
2. `BRICK_1X6`
3. `BRICK_1X4`
4. `BRICK_1X3`
5. `BRICK_1X2`
6. `BRICK_1X1`

Les briques `1 x N` sont tournées d'un quart de tour lorsque nécessaire afin que N soit parallèle à l'axe X du mur.

Le résultat doit être déterministe.

## Exemple

Pour un mur de 17 tenons de large et 2 briques de haut :

- rangée 0 : `1x8 + 1x8 + 1x1`
- rangée 1 : `1x8 + 1x8 + 1x1`

Cette répétition volontaire des joints sera corrigée dans une étape ultérieure consacrée au bond pattern et à la stabilité.
