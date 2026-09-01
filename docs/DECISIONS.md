# Architecture Decision Log

Ce fichier conserve les décisions structurantes afin que les humains et les agents de développement travaillent contre la même référence.

## ADR-001 — Le dépôt existant est conservé

**Décision :** le repository `lego-app` reste le dépôt officiel pendant la phase de fondation. Le nom commercial pourra changer plus tard.

## ADR-002 — Le moteur est indépendant des fournisseurs

**Décision :** les pièces sont manipulées par des identifiants internes. Les références Rebrickable, LDraw et fournisseurs sont des mappings externes.

## ADR-003 — BuildingModel est la représentation centrale du bâtiment

**Décision historique :** les photos ne sont pas converties directement en briques. Elles alimentent une représentation architecturale structurée avant toute projection LEGO.

**Évolution :** le pipeline photo courant a depuis séparé explicitement `ArchitecturalSurvey v0.1` et `ArchitecturalScene v0.2`. `BuildingModel` reste un contrat historique/M0 et un sous-ensemble utile ; il n’est plus l’unique représentation architecturale centrale du workflow photo moderne.

## ADR-004 — Séparation des représentations

**Décision :** ne pas utiliser un objet unique pour tout le pipeline. Les frontières historiques `PhotoEvidence`, `BuildingModel`, `BuildingGeometry`, `BrickModel` et `AssemblyPlan` restent valides comme principe de séparation, et ont été complétées par `ArchitecturalSurvey`, `ArchitecturalScene`, `InstructionPlan`, `BagPlan` et les contrats de validation géométrique.

## ADR-005 — M0 commence sans analyse photo

**Décision historique :** valider d'abord `BuildingModel -> BuildingGeometry -> BrickModel -> AssemblyPlan` avec des bâtiments synthétiques connus. Cette étape est terminée ; le pipeline photo est désormais actif, sans supprimer le rôle du M0 comme socle déterministe/régression.

## ADR-006 — Petit catalogue fiable d'abord

**Décision :** ne pas chercher à supporter immédiatement toutes les pièces disponibles. Commencer par un sous-ensemble géométriquement fiable, puis l'étendre.

## ADR-007 — Les scripts historiques sont conservés mais non officiels

**Décision :** `scripts/build_database.py`, `scripts/build_master_catalog.py` et `scripts/normalize_types.py` sont des travaux exploratoires utiles. Ils restent dans le dépôt, mais ne sont pas encore la chaîne de génération officielle et devront être révisés avant réutilisation.

## ADR-008 — L'échelle du modèle préserve les proportions physiques de la grille

**Décision :** la géométrie réelle reste exprimée en mètres. La maquette choisit une échelle en tenons par mètre, puis la hauteur est dérivée avec la proportion physique de la grille (8 mm par tenon horizontal, 9,6 mm par rangée de brique standard). Les ouvertures sont quantifiées dans la même échelle ; elles ne sont pas redimensionnées indépendamment.

**Conséquence :** un bâtiment complet doit utiliser une échelle globale partagée par toutes ses façades. Le choix d’une largeur cible par mur dans BH-008 est une primitive de validation, pas le mécanisme final de génération bâtiment.

## ADR-009 — Survey = autorité sémantique, Scene = autorité métrique

**Décision :** `ArchitecturalSurvey v0.1` est l’autorité pour l’inventaire observé, les IDs, les certitudes, les relations et les faits sémantiques. `ArchitecturalScene v0.2` est l’autorité pour la reconstruction métrique/géométrique cohérente de ces faits.

**Conséquences :**
- une primitive certaine du Survey ne disparaît pas uniquement parce que sa métrique est difficile ;
- une métrique peut rester inconnue ou `inferred` sans réécrire la certitude d’existence ;
- les preuves photo complémentaires au stade Scene peuvent borner la géométrie mais ne peuvent pas corriger silencieusement l’inventaire Survey validé ;
- les relations certaines visibles doivent être satisfaites géométriquement avant d’être marquées résolues.

## ADR-010 — Les contraintes LEGO ne réécrivent jamais la vérité architecturale

**Décision :** la projection LEGO, le tuilage, les familles de pente, les collisions ou autres contraintes physiques doivent adapter la construction, jamais la Scene architecturale elle-même.

**Conséquences :**
- une longueur de toiture non tileable peut recevoir un surplomb LEGO minimal plutôt que modifier la longueur du bâtiment ;
- une pièce de toiture peut être retirée autour d’une cheminée explicite plutôt que supprimer/déplacer la cheminée ;
- une impossibilité de rendu devient `fidelity_issue` ou limitation explicite ;
- les tests doivent vérifier que les dimensions architecturales restent inchangées lors d’une adaptation LEGO.

## ADR-011 — Le round-trip IA manuel principal est volontairement en deux étapes

**Décision :** avant toute dépendance produit à une API IA, le workflow principal est :
1. Photos → `ArchitecturalSurvey v0.1` ;
2. Survey validé + PDF photo original → `ArchitecturalScene v0.2`.

Le flux historique `external-bundle-0.1` reste seulement une compatibilité d’import.

**Conséquence :** ne pas fusionner à nouveau Survey et Scene dans un unique résultat IA pour simplifier localement l’interface. Le jalon d’acceptation bout-en-bout reste BH-090 / issue #274.

## ADR-012 — Les garde-fous de prompts évoluent par couches additives

**Décision :** lorsqu’un prompt historique est déjà couvert par des régressions, les nouveaux audits génériques doivent être ajoutés sans condenser ni remplacer silencieusement les règles existantes.

**Contexte :** l’ajout de l’audit terrain a montré qu’une réécriture directe du prompt Survey pouvait supprimer des invariants historiques. Le modèle actuel conserve le prompt de base et superpose des audits terrain/topologie via des wrappers versionnés.

**Conséquence :** une future règle de conformité Photos → Survey doit, par défaut, suivre la même stratégie additive et être couverte par tests avant déploiement.

## ADR-013 — Un audit IA indépendant est un diagnostic séparé, jamais une mutation

**Décision :** `SurveyAudit v0.1` est un contrat additif distinct de `ArchitecturalSurvey v0.1`. Il intervient uniquement après validation déterministe du Survey et produit des findings photo-référencés sans réécrire l’objet audité.

**Conséquences :**
- les validateurs Survey existants restent obligatoires et autoritatifs pour les invariants déterministes ;
- l’audit se concentre sur les erreurs que le JSON seul ne permet pas de décider : fidélité visuelle, omissions, identité multi-vues, orientation, relations visibles et calibration de certitude ;
- chaque finding non `insufficient_evidence` doit citer une preuve photo ;
- l’audit n’applique aucune correction automatique ; une éventuelle correction appartient à un futur workflow explicite et traçable ;
- `SceneAudit` reste conditionnel à la mesure d’un gain non redondant après expérimentation de `SurveyAudit`.
