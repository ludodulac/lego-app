# Architecture baseline

Ce document fixe la direction d'architecture avant le développement du moteur.

## Pipeline cible

1. `PhotoEvidence` — faits observés dans les images et informations fournies par l'utilisateur.
2. `BuildingModel` — représentation sémantique et paramétrique du bâtiment.
3. `BuildingGeometry` — géométrie 3D déterministe dérivée du BuildingModel.
4. `BrickModel` — placement des pièces de construction et leurs orientations.
5. `AssemblyPlan` — ordre constructible des étapes de montage.

## Principe central

L'IA n'est pas le moteur de construction. Elle sert principalement à transformer des observations (photos + texte) en informations architecturales structurées. La conversion vers la géométrie, les briques, l'optimisation et l'ordre de montage doit être autant que possible déterministe, testable et reproductible.

## Composants prévus

- Building engine : validation et manipulation du BuildingModel.
- Geometry engine : volumes, murs, ouvertures, toitures et autres primitives architecturales.
- Brick engine : discrétisation et placement de pièces.
- Optimizer : fidélité, stabilité, nombre de pièces, simplicité, disponibilité et coût.
- Assembly engine : génération d'un ordre de construction valide.
- Web viewer : visualisation du BrickModel et de l'AssemblyPlan.

## Données de pièces

Le moteur utilise des identifiants internes indépendants des fournisseurs. Les données Rebrickable actuelles servent de métadonnées et de matière première pour le catalogue ; elles ne constituent pas à elles seules une vérité géométrique.

Les caractéristiques géométriques et les connecteurs devront être décrits explicitement et validés.

## Architecture applicative cible

- Frontend : Next.js / React / TypeScript.
- Backend et moteurs : Python / FastAPI pour l'orchestration et les calculs.
- Persistance SaaS prévue : Supabase (PostgreSQL, Auth, Storage), introduite seulement lorsqu'elle devient nécessaire.
- Calculs lourds : workers séparés si nécessaire ; ne pas coupler le moteur à Supabase Edge Functions.

## Règle de changement

Toute modification importante de cette architecture doit être documentée dans `docs/DECISIONS.md` avant ou avec son implémentation.
