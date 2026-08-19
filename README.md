# BrickHouse AI

> Nom de travail. Le dépôt conserve pour l'instant le nom `lego-app`.

BrickHouse AI transforme une représentation structurée d'un bâtiment en modèle constructible avec des briques de construction compatibles, puis produit une visualisation 3D et une nomenclature de pièces (BOM). Le produit final devra pouvoir partir d'une ou plusieurs photos et d'indications textuelles, mais le moteur M0 est volontairement déterministe avant d'ajouter l'analyse d'images par IA.

## Pipeline actuel

Le cœur M0 fonctionne selon :

`BuildingModel -> BuildingGeometry -> BuildingBrickShell -> SpatialBrickShell + SpatialRoof -> BrickModel -> BOM -> BrickExportBundle`

La cible produit complète reste :

`PhotoEvidence -> BuildingModel -> BuildingGeometry -> BrickModel -> AssemblyPlan`

Les modèles IA ne doivent pas générer directement une liste de briques. Ils devront produire ou enrichir une représentation architecturale structurée, ensuite traitée par les moteurs déterministes.

## Ce que M0 sait déjà faire

- valider un `BuildingModel` structuré en mètres ;
- générer les quatre murs et les ouvertures ;
- appliquer une échelle cohérente à toute la maison ;
- placer des briques autour des portes et fenêtres ;
- décaler les joints entre rangées ;
- lier les quatre façades dans une coque 3D avec angles alternés ;
- générer un premier toit à deux pans en grille ;
- produire un `BrickModel` unique ;
- produire une BOM ;
- exporter le résultat en JSON ;
- afficher ce JSON dans un viewer 3D web.

## Lancer le pipeline M0

Python 3.12+ est requis.

```bash
python -m pip install -e ".[dev]"
brickhouse-m0 docs/examples/building-model-simple-house.json frontend/sample-export.json --front-width-studs 48
```

Le fichier produit est directement lisible par le viewer.

## Lancer le viewer localement

```bash
python -m http.server 8000 --directory frontend
```

Puis ouvrir `http://localhost:8000` dans un navigateur. Le viewer permet rotation, zoom, déplacement, recentrage et chargement d'un export JSON local.

## Tests et intégration continue

```bash
pytest -q
```

Le workflow `.github/workflows/ci.yml` exécute automatiquement la suite de tests et le pipeline de référence sur GitHub Actions pour chaque push sur `main` et chaque pull request.

## Déploiement du viewer

`.github/workflows/pages.yml` est prêt à reconstruire la vraie maison de référence avec le moteur puis à publier `frontend/` sur GitHub Pages. Voir `docs/DEPLOYMENT.md`.

## Structure actuelle

- `backend/brickhouse/building/` — contrat `BuildingModel` et validation ;
- `backend/brickhouse/geometry/` — géométrie architecturale ;
- `backend/brickhouse/bricks/` — catalogue, placement, échelle, coque 3D, toit, BrickModel, BOM et export ;
- `backend/brickhouse/pipeline.py` — pipeline M0 de bout en bout ;
- `frontend/` — viewer 3D statique ;
- `data/raw/` — données sources externes non transformées ;
- `data/processed/` — données dérivées/catalogues exploratoires ;
- `scripts/` — scripts historiques d'import/normalisation, non considérés comme pipeline officiel ;
- `docs/` — spécifications et décisions d'architecture ;
- `tests/` — tests automatisés.

## Catalogue de pièces

Le moteur ne dépend pas des références d'un fournisseur ou d'une marque. Il utilise des identifiants fonctionnels internes, par exemple `BRICK_2X4`. Les références Rebrickable, LDraw ou celles de futurs fournisseurs seront des mappings externes.

Le fichier `data/processed/piece_types_master.csv` est un travail exploratoire conservé, mais il ne constitue pas encore la spécification géométrique définitive du moteur.

## Périmètre encore hors M0

- analyse de photos ;
- génération de questions à l'utilisateur pour les zones invisibles ;
- vraies géométries fournisseur des pièces ;
- optimiseur avancé de stabilité/coût/disponibilité ;
- `AssemblyPlan` et notice de montage ;
- API SaaS, authentification, stockage cloud, paiement ou commande de pièces.

## Règles de développement

1. Une fonctionnalité suit : spécification -> ticket -> développement -> tests -> validation -> commit.
2. Ne pas réinventer l'architecture au fil des implémentations.
3. Ne pas introduire de fournisseur obligatoire dans le moteur.
4. Séparer compréhension architecturale, géométrie, placement des briques, optimisation et ordre de montage.
5. Préserver explicitement les hypothèses et niveaux de confiance lorsque l'analyse photo sera ajoutée.
6. Préférer un petit catalogue géométriquement fiable à un grand catalogue mal défini.

## Statut

Le moteur M0 possède maintenant une chaîne de bout en bout depuis un `BuildingModel` JSON jusqu'au viewer 3D et à la BOM. La prochaine grande phase est de rendre ce résultat réellement constructible/assemblable, puis d'introduire progressivement l'analyse photo.
