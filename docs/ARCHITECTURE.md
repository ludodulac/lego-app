# Architecture baseline

Ce document fixe les frontières structurantes actuelles du projet. Les décisions détaillées et leur historique sont dans `docs/DECISIONS.md`.

## Pipeline cible actuel

1. photos / faits utilisateur ;
2. `ArchitecturalSurvey v0.1` — inventaire observé, identité, certitude, relations, evidence ;
3. raisonnement/fusion architecturale ;
4. `ArchitecturalScene v0.2` — géométrie métrique cohérente du bâtiment et du site ;
5. adaptation déterministe aux capacités LEGO ;
6. `BrickModel` ;
7. validation géométrique / assemblage ;
8. `AssemblyPlan`, `InstructionPlan`, `BagPlan`, BOM et exports/viewer.

Les contrats historiques `BuildingModel` / `BuildingGeometry` restent utilisés par le M0 et plusieurs régressions, mais ils ne décrivent plus à eux seuls tout le workflow photo.

## Principe central

L’IA n’est pas le moteur de construction. Elle transforme des observations en informations architecturales structurées et métriques avec incertitude explicite. La conversion vers les briques, les contrôles physiques, l’optimisation et l’ordre de montage doivent rester autant que possible déterministes, testables et reproductibles.

Frontière de vérité :
- Survey = autorité sémantique/observée ;
- Scene = autorité métrique/géométrique ;
- LEGO = approximation physique de la Scene, jamais réécriture de la Scene.

## Composants actuels

- Survey/Scene engine : validation des contrats architecturaux et cohérence inter-couches.
- Geometry engine architectural : volumes, surfaces, murs, ouvertures, terrain et primitives associées.
- Brick engine : discrétisation, placement, détails Scene-aware et construction du `BrickModel`.
- LEGO Geometry & Assembly Engine : lecture LDraw, transforms, collisions/contacts, containment, support et connecteurs dans le périmètre pris en charge.
- Planning : `AssemblyPlan` pour l’ordre constructif, `InstructionPlan` pour la présentation de montage, `BagPlan` pour la préparation/emballage.
- Web frontend : workflow photo/handoff IA et viewer.

## Données de pièces

Le moteur utilise des identifiants internes indépendants des fournisseurs. Rebrickable, LDraw et futurs fournisseurs sont des mappings/métadonnées externes ; leur présence ne constitue pas à elle seule une preuve de géométrie ou de capacité de placement.

Les capacités géométriques et connecteurs doivent être décrits explicitement et validés avant utilisation déterministe.

## Architecture applicative

L’implémentation réellement présente dans le dépôt prime sur les intentions historiques de stack. Le backend est Python/FastAPI ; le frontend actuellement déployé sur GitHub Pages est un frontend web statique dans `frontend/`.

Une migration future vers React/TypeScript, une persistance SaaS ou Supabase n’est pas une permission de refactorer le chemin actuel tant qu’un besoin produit concret ne la justifie pas.

## Règle de changement

Toute modification importante de ces frontières doit être documentée dans `docs/DECISIONS.md` avant ou avec son implémentation et couverte par des régressions lorsque le comportement est exécutable.
