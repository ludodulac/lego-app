# Architecture Decision Log

Ce fichier conserve les décisions structurantes afin que les humains et les agents de développement travaillent contre la même référence.

## ADR-001 — Le dépôt existant est conservé

**Décision :** le repository `lego-app` reste le dépôt officiel pendant la phase de fondation. Le nom commercial pourra changer plus tard.

## ADR-002 — Le moteur est indépendant des fournisseurs

**Décision :** les pièces sont manipulées par des identifiants internes. Les références Rebrickable, LDraw et fournisseurs sont des mappings externes.

## ADR-003 — BuildingModel est la représentation centrale du bâtiment

**Décision :** les photos ne sont pas converties directement en briques. Elles alimenteront un `PhotoEvidence`, puis un `BuildingModel` paramétrique.

## ADR-004 — Séparation des représentations

**Décision :** ne pas utiliser un objet unique pour tout le pipeline. Les contrats principaux sont `PhotoEvidence`, `BuildingModel`, `BuildingGeometry`, `BrickModel` et `AssemblyPlan`.

## ADR-005 — M0 commence sans analyse photo

**Décision :** valider d'abord `BuildingModel -> BuildingGeometry -> BrickModel -> AssemblyPlan` avec des bâtiments synthétiques connus. L'analyse photo sera ajoutée ensuite.

## ADR-006 — Petit catalogue fiable d'abord

**Décision :** ne pas chercher à supporter immédiatement toutes les pièces disponibles. Commencer par un sous-ensemble géométriquement fiable, puis l'étendre.

## ADR-007 — Les scripts historiques sont conservés mais non officiels

**Décision :** `scripts/build_database.py`, `scripts/build_master_catalog.py` et `scripts/normalize_types.py` sont des travaux exploratoires utiles. Ils restent dans le dépôt, mais ne sont pas encore la chaîne de génération officielle et devront être révisés avant réutilisation.

## ADR-008 — L'échelle du modèle préserve les proportions physiques de la grille

**Décision :** la géométrie réelle reste exprimée en mètres. La maquette choisit une échelle en tenons par mètre, puis la hauteur est dérivée avec la proportion physique de la grille (8 mm par tenon horizontal, 9,6 mm par rangée de brique standard). Les ouvertures sont quantifiées dans la même échelle ; elles ne sont pas redimensionnées indépendamment.

**Conséquence :** un bâtiment complet devra utiliser une échelle globale partagée par toutes ses façades. Le choix d'une largeur cible par mur dans BH-008 est une primitive de validation, pas le mécanisme final de génération bâtiment.
