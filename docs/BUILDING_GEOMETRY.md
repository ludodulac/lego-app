# BuildingGeometry v0.1

`BuildingGeometry` est la représentation géométrique déterministe dérivée d'un `BuildingModel` validé.

Elle ne contient ni briques, ni fournisseurs, ni étapes de montage, ni mesh photogrammétrique.

## Objectif

Produire des surfaces architecturales simples, exactes et reproductibles qui serviront d'entrée au futur moteur de conversion en briques.

## Représentations

### WallGeometry

Chaque volume rectangulaire produit quatre murs : `front`, `rear`, `left`, `right`.

Chaque mur contient quatre coins 3D et la liste de ses ouvertures déjà converties en rectangles 3D.

L'ordre des coins suit l'orientation extérieure de la façade. Cela garantit que `offset_horizontal` reste mesuré depuis la gauche lorsque la façade est regardée depuis l'extérieur.

### OpeningGeometry

Une ouverture conserve son ID, son type, son volume et sa façade. Ses quatre coins sont exprimés dans le repère global du projet.

Aucune soustraction booléenne n'est effectuée en v0.1 : le mur reste une surface rectangulaire et porte explicitement ses zones d'ouverture.

### RoofPlaneGeometry

Une toiture plate produit un plan rectangulaire.

Une toiture à deux pans produit deux plans. La hauteur du faîtage est calculée à partir de l'angle :

`ridge_height = eave_height + tan(pitch) * half_span`

Le débord de toiture est inclus dans la portée inclinée, donc il augmente également la hauteur du faîtage pour conserver exactement le même angle de pente jusqu'au bord du toit.

## Non-objectifs v0.1

- triangulation / mesh ;
- épaisseur réelle des murs ;
- opérations booléennes entre volumes ;
- suppression des surfaces internes entre volumes adjacents ;
- détails de fenêtres et portes ;
- charpente ;
- gouttières ;
- géométrie courbe ;
- placement de briques.

## API

```python
from brickhouse.geometry import generate_building_geometry

geometry = generate_building_geometry(building_model)
```

La fonction doit être déterministe : un même `BuildingModel` doit produire une sérialisation identique.
