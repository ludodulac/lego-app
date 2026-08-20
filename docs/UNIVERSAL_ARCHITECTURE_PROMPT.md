# BrickHouse — contrat de prompt universel

Objectif : permettre à une IA externe disposant d'une ou plusieurs photos de produire une analyse réutilisable par BrickHouse, sans dépendre de son fournisseur.

## Principe

Le prompt universel ne demande jamais « fais-moi une maison LEGO ». Il demande une **description architecturale structurée** que BrickHouse pourra ensuite valider et convertir.

L'IA doit effectuer deux analyses distinctes :
1. `semantic_analysis` : ce que les éléments semblent être et comment ils sont liés ;
2. `geometric_analysis` : proportions, coordonnées relatives, rotations, dimensions estimées et preuves.

Puis elle produit `scene` : synthèse paramétrique issue des deux analyses.

## Règles obligatoires

- Ne jamais mesurer directement une distance réelle à partir des pixels sans corriger la perspective.
- Croiser toutes les images de la même construction.
- Une mesure réelle fournie par l'utilisateur sert d'ancre globale.
- Toute valeur non déterminable peut être `null`.
- Ne jamais inventer une face cachée sans la marquer `inferred`.
- Chaque valeur importante doit comporter `source` et `confidence`.
- Les hypothèses doivent être séparées des observations.
- Les formes atypiques doivent être décrites par composition de volumes/transforms plutôt que forcées dans une catégorie de maison standard.
- Si une forme ne peut pas être représentée avec les primitives disponibles, créer un `unsupported_geometry` décrivant ce qui manque plutôt que la remplacer silencieusement.

## Enveloppe JSON cible

```json
{
  "schema_version": "brickhouse-scene-0.1",
  "semantic_analysis": {
    "building_type": null,
    "components": [],
    "architectural_features": [],
    "occlusions": [],
    "hypotheses": []
  },
  "geometric_analysis": {
    "scale_basis": null,
    "reference_axes": [],
    "proportion_evidence": [],
    "view_relationships": [],
    "uncertainties": []
  },
  "scene": {
    "units": "m",
    "nodes": [],
    "relations": [],
    "surfaces": [],
    "openings": []
  },
  "questions": [],
  "global_confidence": 0.0
}
```

## Noeud de scène cible

Chaque noeud doit pouvoir contenir :

```json
{
  "id": "volume_01",
  "kind": "box|prism|cylinder|extrusion|roof_surface|custom",
  "semantic_role": "main_building|extension|tower|bay_window|chimney|terrace|other",
  "transform": {
    "position": {"x": null, "y": null, "z": null},
    "rotation_degrees": {"x": null, "y": null, "z": null},
    "dimensions": {"x": null, "y": null, "z": null}
  },
  "source": "observed|user_provided|inferred|estimated",
  "confidence": 0.0,
  "evidence": []
}
```

Cette structure est volontairement extensible. Le logiciel ne doit pas exiger que toutes les valeurs soient remplies.

## Usage externe

À terme, l'utilisateur pourra copier un prompt BrickHouse dans ChatGPT, Gemini ou une autre IA, joindre ses photos et récupérer ce JSON. BrickHouse proposera alors un import « Analyse externe » qui valide le schéma, affiche les inconnues/questions, puis normalise la scène vers les capacités actuelles du moteur LEGO.

Le JSON produit par une IA externe est toujours traité comme **non fiable jusqu'à validation du schéma et des contraintes géométriques**.