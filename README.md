# BrickHouse AI

> Nom de travail. Le dépôt conserve pour l'instant le nom `lego-app`.

BrickHouse AI est un projet de logiciel destiné à transformer la représentation d'un bâtiment (maison, immeuble, partie d'appartement, etc.) en un modèle constructible avec des briques de construction compatibles, puis à produire une visualisation 3D, une nomenclature de pièces (BOM) et, à terme, une notice de montage.

Le produit final devra pouvoir partir d'une ou plusieurs photos et d'indications textuelles. Toutefois, le développement commence volontairement par le cœur déterministe du système : construire correctement une maison paramétrique connue avant d'ajouter l'analyse d'images par IA.

## Principe d'architecture

Le pipeline cible est :

`PhotoEvidence -> BuildingModel -> BuildingGeometry -> BrickModel -> AssemblyPlan`

Pour la première milestone (M0), le pipeline commence directement à `BuildingModel`.

Les modèles IA ne doivent pas générer directement une liste de briques. Ils doivent produire ou enrichir une représentation architecturale structurée, ensuite traitée par les moteurs déterministes.

## Milestone M0 — Digital Brick House

Objectif : à partir d'une description structurée d'une maison simple, générer automatiquement un modèle en briques, l'afficher en 3D et produire une BOM exacte.

M0 n'inclut pas encore :

- analyse de photos ;
- API OpenAI ou Anthropic dans le produit ;
- paiement ;
- commande de pièces ;
- fournisseur obligatoire ;
- application mobile native ;
- infrastructure cloud complexe.

## Structure actuelle

- `backend/` — futur backend/API (prévu en Python/FastAPI).
- `frontend/` — future application web.
- `data/raw/` — données sources externes non transformées.
- `data/processed/` — données dérivées et catalogues expérimentaux.
- `data/database/` — emplacement réservé aux données/base locale si nécessaire.
- `scripts/` — scripts expérimentaux d'import, normalisation et construction de catalogue.
- `docs/` — spécifications et décisions d'architecture.
- `tests/` — tests automatisés à venir.

## Catalogue de pièces

Règle fondamentale : le moteur ne doit pas dépendre des références d'un fournisseur ou d'une marque.

Il utilise des identifiants fonctionnels internes, par exemple `BRICK_2X4`. Les références Rebrickable, LDraw ou celles de futurs fournisseurs seront des mappings externes.

Le fichier `data/processed/piece_types_master.csv` est un travail exploratoire existant. Il est conservé, mais il ne constitue pas encore la spécification géométrique définitive du moteur.

## Scripts existants

Les scripts présents dans `scripts/` proviennent de la phase exploratoire précédente. Ils sont conservés afin de ne perdre aucun travail, mais leur pipeline n'est pas encore considéré comme stable.

En particulier, certains attendent des fichiers intermédiaires qui ne sont pas actuellement présents ou rangés aux emplacements historiques. Ne pas considérer ces scripts comme la chaîne de build officielle tant qu'ils n'ont pas été révisés.

## Règles de développement

1. Une fonctionnalité suit : spécification -> ticket -> développement -> tests -> validation -> commit.
2. Ne pas réinventer l'architecture au fil des implémentations.
3. Ne pas introduire de fournisseur obligatoire dans le moteur.
4. Séparer compréhension architecturale, géométrie, placement des briques, optimisation et ordre de montage.
5. Préserver explicitement les hypothèses et niveaux de confiance lorsque l'analyse photo sera ajoutée.
6. Préférer un petit catalogue géométriquement fiable à un grand catalogue mal défini.

## Prochaines étapes

- BH-002 : spécifier `BuildingModel`.
- Définir ensuite `BuildingGeometry`, `BrickModel` et `AssemblyPlan`.
- Construire un catalogue minimal de pièces pour le moteur.
- Générer les premiers murs et bâtiments synthétiques avant de brancher l'IA photo.

## Statut

Projet en phase de fondation technique. Les données historiques et scripts exploratoires ont été conservés intentionnellement pendant la restructuration.
