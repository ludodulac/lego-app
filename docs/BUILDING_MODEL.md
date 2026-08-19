# BuildingModel v0.1

`BuildingModel` est la représentation sémantique et paramétrique centrale d'un bâtiment avant sa conversion en géométrie puis en briques.

Il ne doit contenir ni références de pièces, ni logique fournisseur, ni étapes de montage.

## Objectif de la version 0.1

Supporter les bâtiments simples de la milestone M0 :

- un ou plusieurs volumes rectangulaires ;
- 1 à 3 niveaux ;
- murs verticaux ;
- portes et fenêtres rectangulaires ;
- toiture plate ou à deux pans ;
- couleurs/matériaux simplifiés ;
- informations certaines, supposées ou fournies par l'utilisateur.

Les balcons complexes, toitures courbes, murs non orthogonaux, arches, escaliers complexes et détails décoratifs sont reportés.

## Unités et repère

Toutes les dimensions du `BuildingModel` sont exprimées en mètres.

Repère local du projet :

- X : gauche -> droite vu depuis la façade avant ;
- Y : avant -> arrière ;
- Z : bas -> haut.

L'origine `(0, 0, 0)` correspond au coin avant-gauche du volume principal au niveau du sol.

## Structure racine

```json
{
  "schema_version": "0.1",
  "id": "building_001",
  "name": "Maison test",
  "building_type": "detached_house",
  "units": "m",
  "volumes": [],
  "openings": [],
  "roofs": [],
  "appearance": {},
  "metadata": {}
}
```

## Volumes

Un bâtiment est composé d'un ou plusieurs volumes architecturaux simples.

```json
{
  "id": "vol_main",
  "shape": "rectangular_prism",
  "position": {"x": 0, "y": 0, "z": 0},
  "width": 10.0,
  "depth": 8.0,
  "height": 5.6,
  "floors": 2,
  "source": {
    "kind": "user_provided",
    "confidence": 1.0
  }
}
```

### Règles

- `width`, `depth`, `height` > 0.
- `floors` est un entier >= 1.
- En v0.1, `shape` vaut uniquement `rectangular_prism`.
- Les volumes peuvent se chevaucher ou être adjacents ; la fusion géométrique appartient à `BuildingGeometry`.

## Façades

Chaque face verticale d'un volume rectangulaire possède un nom logique :

- `front`
- `rear`
- `left`
- `right`

Ces noms servent notamment au placement des ouvertures.

## Ouvertures

Une ouverture appartient à une façade d'un volume.

```json
{
  "id": "window_front_01",
  "type": "window",
  "volume_id": "vol_main",
  "facade": "front",
  "offset_horizontal": 2.0,
  "offset_vertical": 1.0,
  "width": 1.2,
  "height": 1.3,
  "source": {
    "kind": "observed",
    "confidence": 0.95
  }
}
```

`offset_horizontal` est mesuré depuis le bord gauche de la façade lorsqu'on la regarde depuis l'extérieur.

`offset_vertical` est mesuré depuis le bas du volume.

Types autorisés en v0.1 :

- `window`
- `door`
- `garage_door`

### Règles

- Une ouverture doit tenir entièrement dans la façade ciblée.
- Deux ouvertures ne doivent pas se superposer, sauf future exception explicitement gérée.
- La géométrie du cadre, du vitrage et des détails n'appartient pas au BuildingModel v0.1.

## Toitures

Deux types sont supportés en v0.1.

### Toiture plate

```json
{
  "id": "roof_main",
  "volume_id": "vol_main",
  "type": "flat",
  "overhang": 0.2,
  "source": {"kind": "observed", "confidence": 0.9}
}
```

### Toiture à deux pans

```json
{
  "id": "roof_main",
  "volume_id": "vol_main",
  "type": "gable",
  "ridge_direction": "depth",
  "pitch_degrees": 35,
  "overhang": 0.3,
  "source": {"kind": "observed", "confidence": 0.9}
}
```

`ridge_direction` :

- `width` : faîtage parallèle à X ;
- `depth` : faîtage parallèle à Y.

## Apparence

L'apparence est volontairement simple en v0.1.

```json
{
  "walls": {
    "color": "light_beige"
  },
  "roof": {
    "color": "dark_red"
  },
  "frames": {
    "color": "white"
  }
}
```

Les couleurs sont des identifiants internes logiques. Le mapping vers des couleurs de pièces réelles appartient à une couche ultérieure.

## Provenance et confiance

Tout élément important peut porter :

```json
{
  "kind": "observed",
  "confidence": 0.92
}
```

Valeurs de `kind` :

- `observed` — directement visible dans une ou plusieurs images ;
- `user_provided` — explicitement indiqué par l'utilisateur ;
- `inferred` — déduit par le système ;
- `generated_default` — valeur de repli choisie faute d'information.

`confidence` est compris entre 0 et 1.

Règle : une valeur `user_provided` est considérée comme prioritaire sur une valeur `observed`, sauf future correction explicite de l'utilisateur.

## Métadonnées

```json
{
  "created_from": "synthetic",
  "notes": "Maison de test M0"
}
```

Valeurs prévues de `created_from` :

- `synthetic`
- `photo_analysis`
- `user_edit`

## Invariants de v0.1

1. Le modèle est indépendant des briques et fournisseurs.
2. Les dimensions sont en mètres.
3. Les positions sont dans un repère local unique.
4. Chaque objet possède un `id` stable dans le modèle.
5. Les références entre objets utilisent ces IDs.
6. Une ouverture dépend d'un volume et d'une façade.
7. Une toiture dépend d'un volume.
8. La provenance et la confiance restent séparées de la valeur géométrique.
9. `BuildingModel` décrit ce que le bâtiment est ; `BuildingGeometry` décide comment produire la géométrie exacte.
10. Toute extension du schéma doit rester rétrocompatible dans une même version majeure, ou incrémenter `schema_version`.

## Hors périmètre v0.1

- objets intérieurs ;
- mobilier ;
- terrain ;
- arbres et végétation ;
- bâtiments courbes ;
- murs inclinés ;
- toitures complexes ou courbes ;
- escaliers paramétriques ;
- balcons détaillés ;
- gouttières ;
- textures photoréalistes ;
- références de pièces ;
- prix, fournisseurs, stock ;
- contraintes de montage.
