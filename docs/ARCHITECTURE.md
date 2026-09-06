# Architecture baseline

Ce document fixe les frontières structurantes actuelles du projet. Les décisions détaillées et leur historique sont dans `docs/DECISIONS.md`.

## Pipeline cible actuel

1. photos / faits utilisateur ;
2. `ArchitecturalSurvey v0.1` — inventaire observé, identité, certitude, relations, evidence ;
3. raisonnement/fusion architecturale ;
4. `ArchitecturalScene v0.2` — géométrie métrique **et topologie spatiale cohérente** du bâtiment et du site ;
5. validation de vérité spatiale : enveloppes, ordre, niveaux, contacts, supports, recouvrements, retraits/débords et relations entre objets ;
6. plan de représentation LEGO — choix des familles/assemblages architecturaux réellement supportés et réservation de leurs empreintes ;
7. adaptation/optimisation LEGO bornée autour de ces ancres, puis remplissage résiduel ;
8. `BrickModel` ;
9. validation physique : collisions, contacts, connecteurs et chaîne d'appui/connexion jusqu'à une structure porteuse ;
10. `AssemblyPlan`, `InstructionPlan`, `BagPlan`, BOM et exports/viewer.

Les contrats historiques `BuildingModel` / `BuildingGeometry` restent utilisés par le M0 et plusieurs régressions, mais ils ne décrivent plus à eux seuls tout le workflow photo.

## Principe central

L’IA n’est pas le moteur de construction. Elle transforme des observations en informations architecturales structurées et métriques avec incertitude explicite. La conversion vers les briques, les contrôles physiques, l’optimisation et l’ordre de montage doivent rester autant que possible déterministes, testables et reproductibles.

Frontière de vérité :
- Survey = autorité sémantique/observée ;
- Scene = autorité métrique, géométrique **et spatiale/topologique** ;
- plan LEGO = décision explicite de représentation à catalogue connu, sans mutation de Survey/Scene ;
- BrickModel = réalisation physique de ce plan ;
- LEGO = approximation physique de la Scene, jamais réécriture de la Scene.

## La Scene n'est pas un sac de coordonnées

Avant toute adaptation LEGO, chaque objet architectural pertinent doit être situé relativement aux autres avec le niveau de précision permis par les preuves. Pour un volume, une toiture, une cheminée, une ouverture, une terrasse, un palier, un escalier, un poteau ou le terrain, le moteur doit pouvoir représenter ou laisser explicitement inconnu :

- enveloppe spatiale et orientation ;
- gauche/droite, avant/arrière, dessus/dessous ;
- niveaux et plages d'altitude ;
- contact, connexion et support ;
- chevauchement/intersection ;
- encastrement/retrait ;
- débord/protrusion et extents relatifs ;
- relations de traversée, par exemple une cheminée qui traverse un pan de toiture ;
- relation au volume/façade/surface qui sert d'ancre.

Une relation certaine du Survey qui devrait avoir une conséquence géométrique ne peut pas être déclarée résolue par simple proximité. Les tolérances de contact sont des contrats explicites. Une contradiction spatiale bloquante doit arrêter la projection LEGO au lieu d'être compensée silencieusement plus tard.

## Plan de représentation LEGO avant remplissage

Le moteur ne doit pas construire un mur générique puis essayer d'y faire rentrer les objets architecturaux. Les éléments à forte identité sont des **ancres LEGO**.

Pour chaque ouverture ou élément caractéristique, une phase de planification recherche d'abord les familles/assemblages réellement disponibles dans le vocabulaire validé : fenêtre, porte, baie, toiture, cheminée, terrasse, garde-corps, escalier, etc. Le choix possède une empreinte LEGO réelle (studs, plates/bricks, profondeur, orientations, connecteurs et marges nécessaires).

L'ordre cible est donc :

`Scene immuable → choix d'assemblages compatibles → réservation des empreintes → résolution des conflits → redistribution bornée de l'espace résiduel → remplissage des murs/surfaces`.

Un ajustement LEGO local est autorisé uniquement dans une tolérance de représentation explicite et traçable. Il ne peut pas changer le côté, l'ordre, le niveau ou une relation caractéristique d'un objet. Par exemple, déplacer légèrement un trumeau peut être acceptable ; déplacer une terrasse sur une autre façade ou une cheminée pour faciliter le tuilage ne l'est pas.

## Constructibilité = porte de sortie obligatoire

Une pièce visuellement proche d'une autre n'est pas pour autant supportée. Avant export, le BrickModel doit pouvoir justifier une chaîne physique de support/connexion pour chaque pièce ou sous-assemblage qui en a besoin : tenons/tubes, empilage, SNOT, clips, charnières ou autre connexion explicitement modélisée.

Une tuile de toiture, un garde-corps, un plateau de terrasse ou un détail flottant est une erreur de constructibilité. Les validations doivent distinguer au minimum : collision, absence de contact, contact non connectable, absence de support et chaîne de support interrompue. L'objectif à terme est une chaîne vers le sol ou une structure porteuse, pas seulement une absence de collision.

## Hiérarchie des contraintes

1. **Invariants architecturaux** : identité, côté, ordre, niveaux, topologie, relations certaines et éléments caractéristiques établis.
2. **Tolérances de représentation LEGO** : petits ajustements locaux quantifiés et tracés qui préservent les invariants.
3. **Contraintes physiques absolues** : pièces réellement disponibles/capables, connexions valides, supports, absence de collisions impossibles et ordre d'assemblage réalisable.

Une optimisation tardive ne peut pas sacrifier une catégorie supérieure pour améliorer un détail local.

## Composants actuels

- Survey/Scene engine : validation des contrats architecturaux et cohérence inter-couches.
- Geometry engine architectural : volumes, surfaces, murs, ouvertures, terrain et primitives associées.
- Brick engine : discrétisation, placement, détails Scene-aware et construction du `BrickModel`.
- LEGO Geometry & Assembly Engine : lecture LDraw, transforms, collisions/contacts, containment, support et connecteurs dans le périmètre pris en charge.
- Planning : `AssemblyPlan` pour l’ordre constructif, `InstructionPlan` pour la présentation de montage, `BagPlan` pour la préparation/emballage.
- Web frontend : workflow photo/handoff IA et viewer.

La phase « plan de représentation LEGO » est une frontière cible à rendre explicite progressivement. Tant qu'elle n'est pas matérialisée par un contrat dédié, les implémentations intermédiaires doivent néanmoins respecter l'ordre ancres → réservation → remplissage et ne pas faire passer un comportement local existant pour la frontière finale.

## Données de pièces

Le moteur utilise des identifiants internes indépendants des fournisseurs. Rebrickable, LDraw et futurs fournisseurs sont des mappings/métadonnées externes ; leur présence ne constitue pas à elle seule une preuve de géométrie ou de capacité de placement.

Les capacités géométriques et connecteurs doivent être décrits explicitement et validés avant utilisation déterministe. Le choix d'une pièce architecturale doit se faire contre ce vocabulaire validé avant que son empreinte ne devienne une contrainte de remplissage.

## Architecture applicative

L’implémentation réellement présente dans le dépôt prime sur les intentions historiques de stack. Le backend est Python/FastAPI ; le frontend actuellement déployé sur GitHub Pages est un frontend web statique dans `frontend/`.

Une migration future vers React/TypeScript, une persistance SaaS ou Supabase n’est pas une permission de refactorer le chemin actuel tant qu’un besoin produit concret ne la justifie pas.

## Règle de changement

Toute modification importante de ces frontières doit être documentée dans `docs/DECISIONS.md` avant ou avec son implémentation et couverte par des régressions lorsque le comportement est exécutable.
