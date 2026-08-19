# Wall openings on the brick grid

BH-007 ajoute la capacité de construire un mur autour de portes et fenêtres rectangulaires, une fois ces ouvertures exprimées sur la grille de briques.

## Représentation

Une ouverture est décrite par :

- `id`
- `x_studs` : position horizontale en tenons depuis le bord gauche du mur
- `z_bricks` : rangée de brique de départ depuis le bas du mur
- `width_studs` : largeur en tenons
- `height_bricks` : hauteur en rangées de briques standard

Exemple :

```python
WallOpeningGrid(
    id="door",
    x_studs=6,
    z_bricks=0,
    width_studs=4,
    height_bricks=3,
)
```

## Génération

`generate_wall_layout_with_openings(width_studs, height_bricks, openings)` :

1. valide les ouvertures ;
2. détermine pour chaque rangée les intervalles interdits ;
3. découpe la matière restante en segments constructibles ;
4. remplit chaque segment avec les briques canoniques `1xN` ;
5. conserve autant que possible la règle de décalage des joints de BH-006 ;
6. ne place aucune brique à l'intérieur d'une ouverture.

Les ouvertures doivent être entièrement contenues dans le mur et ne doivent pas se chevaucher. Deux ouvertures qui se touchent par leur bord sont autorisées.

`generate_simple_wall_layout()` reste disponible et délègue à ce moteur avec une liste d'ouvertures vide.

## Limite volontaire

BH-007 ne convertit pas encore les dimensions architecturales en mètres vers cette grille. Cette conversion dépend de l'échelle finale choisie pour la maquette.

Par exemple, une façade réelle de 10 mètres peut devenir 32, 48 ou 64 tenons selon la taille de modèle désirée. Il serait donc incorrect de figer une conversion mètres → tenons avant d'introduire explicitement ce paramètre d'échelle.

La prochaine couche devra définir cette politique de mise à l'échelle et de discrétisation.
