# Boldüngo / BrickHouse — reprise immédiate de conversation

Date : 2026-08-29

> À lire après `docs/PASSATION_CHATGPT.md` et `docs/JURIDIQUE_ET_VENTE_BRIQUES.md`. Ensuite vérifier l’état réel de `main`, des issues, PR et CI. `main` reste la source technique de vérité si ce document vieillit.

## 1. Discipline de reprise

- dépôt : `ludodulac/lego-app` ; branche de vérité : `main` ;
- travailler de façon autonome par tranches substantielles : inspection -> correction minimale -> régressions -> CI -> merge -> contrôle post-merge ;
- ne solliciter l’utilisateur que lorsqu’une information ou action humaine est réellement nécessaire ;
- ne jamais inventer une géométrie ou une donnée d’approvisionnement pour obtenir un résultat complet ;
- préserver l’existant : une nouvelle couche doit être additive tant qu’une migration destructive n’est pas justifiée ;
- distinguer la marque visible **Boldüngo** des identifiants/packages internes historiques BrickHouse ; ne pas renommer mécaniquement le dépôt ou les imports.

## 2. État fiable atteint le 29/08/2026

### BH-087 — évidence visuelle des volets dans le build déployé

Terminé et réellement vérifié après déploiement.

- Le Scene CLI accepte un overlay optionnel d’évidence `opening_visual` ; seuls les champs explicitement présents sont fusionnés et un ID d’ouverture inconnu échoue clairement.
- La scène de base `tests/fixtures/brickhouse_scene_current.json` reste inchangée.
- `tests/fixtures/real_house_5_shutter_observations.json` cible les IDs canoniques actuels :
  - `front_window_upper_left`
  - `front_window_upper_right`
  - `front_window_middle_right`
  - `right_window_upper`
- `front_window_middle_left` est explicitement conservée sans volets.
- Un premier merge avait rendu la CI verte mais Pages rouge : le chemin `--allow-partial` conservait l’évidence dans ArchitecturalScene sans appliquer `augment_brick_model_with_scene_shutters` au BrickModel.
- Ce défaut de frontière est désormais couvert par un vrai test `write_scene_export(... allow_partial=True, opening_visual_evidence=...)`.
- Correctif final fusionné sur `main` au commit `d50d2370affb90cddc42daa60acac48276446c27` ; le déploiement GitHub Pages correspondant a réussi.
- Issue #266 / BH-087 fermée comme terminée.

Leçon à préserver : une CI de modèles/unités ne suffit pas si Pages exerce un chemin de pipeline différent. Toute exigence de déploiement critique doit aussi être reproduite dans la suite normale de tests.

### BH-088 — InstructionPlan séparé

Terminé et fusionné sur `main` au commit `010312e16072ec3f95444f597f223a2c453f7e7a`.

Le dépôt possède maintenant un contrat renderer-neutral `InstructionPlan` / `InstructionStep`, dérivé déterministement de `AssemblyPlan`.

Il conserve exactement les sémantiques utiles à une notice :
- identifiant et ordre des étapes ;
- placements ;
- phase ;
- `instruction_kind` (`placement` / `subassembly`) ;
- `focus` ;
- `view` backend.

`InstructionPlan` ne contient volontairement pas de numéro de sac. `AssemblyPlan` reste la source d’ordre de construction et reste exporté pour compatibilité. `BrickExportBundle.instruction_plan` est additif.

Quand le pipeline partiel enrichit un BrickModel après création du bundle, il régénère ensemble BOM, AssemblyPlan et InstructionPlan pour éviter un plan de notice périmé.

### BH-089 — BagPlan séparé

Terminé et fusionné sur `main` au commit `99ce6569b57fe0fa9f2750c7067e0c8ea6411004`.

Le dépôt possède maintenant `BagPlan` / `BagGroup`, séparé de la notice. La première version projette volontairement les affectations de sacs historiques d’AssemblyPlan afin de créer une frontière compatible avant toute optimisation d’emballage.

Chaque groupe de sac conserve :
- numéro de sac ;
- phase(s) ;
- IDs d’étapes AssemblyPlan dans l’ordre ;
- IDs de placements complets dans l’ordre.

Les validateurs imposent numérotation contiguë, couverture unique et comptage complet. `BrickExportBundle.bag_plan` est additif ; l’ancien `AssemblyStep.bag` reste présent pendant la migration. Le pipeline partiel régénère également BagPlan après enrichissement.

Cette séparation donne maintenant :

`BrickModel -> AssemblyPlan (construction) -> InstructionPlan (présentation de montage)`

et, séparément :

`AssemblyPlan -> BagPlan (préparation/emballage)`

Les futures optimisations de sacs ne doivent jamais changer l’ordre de construction ni la fidélité architecturale.

## 3. Pipeline manuel Boldüngo -> ChatGPT avant API

Ne pas repartir de zéro : un handoff manuel existe déjà.

`frontend/brickhouse-single-package.js` construit `BRICKHOUSE-ANALYSE-COMPLETE.pdf`, version `pdf-handoff-0.2`.

Le PDF contient :
- la commande complète ;
- les prompts Topologie / Survey / Survey->Scene ;
- les faits utilisateur et l’autorité d’orientation ;
- les **photos elles-mêmes comme pages du PDF**, pas de simples chemins locaux.

La sortie exigée est `brickhouse-external-result.json` avec l’enveloppe :
- `schema_version: external-bundle-0.1`
- `kind: brickhouse_external_result`
- un `ArchitecturalSurvey v0.1` complet ;
- une `ArchitecturalScene v0.2` complète.

Un échec historique important doit rester dans les régressions : une IA avait renvoyé une topologie/résumé à la place d’un Survey complet ; le backend/import avait correctement refusé le JSON. Ne jamais assouplir les contrats pour accepter ce type de sortie malformée.

Issue ouverte #274 / **BH-090 — Validate the manual Boldüngo -> ChatGPT round-trip contract end to end**.

Première tranche recommandée sans intervention utilisateur :
1. expliciter le contrat de round-trip dans le dépôt ;
2. fixture canonique `external-bundle-0.1` ;
3. tests positifs de parse/validation Survey + Scene ;
4. tests négatifs pour les pseudo-Survey/pseudo-Scene de type topologie ;
5. vérifier que générateur frontend et importeur attendent exactement les mêmes version/kind/noms ;
6. seulement après cela, demander un nouveau run humain complet et importer le JSON retourné sans correction manuelle.

La cible produit reste zéro à deux échanges supplémentaires, uniquement lorsqu’une question apporte un gain d’information architectural important.

## 4. Ce qu’il ne faut pas faire ensuite

- Ne pas passer au scraping/catalogue fournisseur massif avant de stabiliser le contrat manuel ChatGPT.
- Ne pas confondre `semantic_color` observée avec une couleur physique réellement disponible chez un fabricant.
- Ne pas optimiser les coûts en supprimant silencieusement un détail caractéristique.
- Ne pas rendre le client captif d’un seul fournisseur.
- Ne pas intégrer bags, instructions et procurement dans un même modèle monolithique : les frontières viennent précisément d’être séparées.
- Ne pas demander à l’utilisateur de refaire un travail humain tant qu’un défaut de contrat ou de pipeline peut encore être testé automatiquement.

## 5. Trajectoire après BH-090

Une fois le round-trip manuel robuste :

1. tester plusieurs maisons / cas afin de valider que le contrat n’est pas benchmark-spécifique ;
2. enrichir InstructionPlan : pages/chapitres, rotations/zooms réellement utiles, sous-assemblages plus riches ;
3. faire évoluer BagPlan vers PackingPlan en gardant la construction indépendante ;
4. consolider le catalogue abstrait fabricant-indépendant (`PartDesign` / éléments fournisseur / couleurs réelles / disponibilité / prix) ;
5. construire ProcurementPlan/comparaison fournisseurs ;
6. seulement ensuite remplacer progressivement l’étape ChatGPT manuelle par API, sans changer le contrat métier validé.

Toujours vérifier l’état réel de GitHub avant d’agir : les commits et numéros ci-dessus sont un point de reprise, pas une permission d’ignorer `main`.
