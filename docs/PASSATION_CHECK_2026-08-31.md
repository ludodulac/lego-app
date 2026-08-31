# Contrôle de passation — 2026-08-31

Ce fichier matérialise le contrôle demandé par `AI_START_HERE.md`. L’état vivant reste `docs/CURRENT_PROJECT_STATE.md`.

## 1. Main / PR / CI / déploiement

- PR #306 `docs: complete AI handoff and continuity index` : fusionnée.
- Merge vérifié : `efb9095f3d249d5f27efea246d68c004145aa2ef`.
- CI de `main` après #306 : run 1259, succès.
- GitHub Pages après #306 : run 515, succès.
- PR historique #296 : fermée comme supersédée par #306, historique conservé.
- BH-090 / issue #274 : commentaire de continuité ajouté avec le dernier benchmark, #305/#306 et les contrôles encore ouverts.

La petite clôture documentaire qui actualise ce fichier ne change aucun comportement produit. Comme toujours, le prochain agent doit revérifier le `main` alors courant et ses workflows avant de travailler.

## 2. Inventaire de la passation

Indexé ou mis à jour :
- `AI_START_HERE.md` — point d’entrée et protocole canonique ;
- `README.md` — pipeline produit actuel ;
- `NEXT_CONVERSATION.md` — reprise immédiate actuelle ;
- `HANDOFF.md` — pointeur non contradictoire ;
- `docs/HANDOFF_HISTORY_2026-08-23.md` — ancien contexte utile conservé ;
- `docs/CURRENT_PROJECT_STATE.md` — état vérifié, benchmark, limites, ouverts, prochaine étape ;
- `docs/ARCHITECTURE.md` — pipeline Survey/Scene/LEGO actuel ;
- `docs/DECISIONS.md` — autorités Survey/Scene, frontière LEGO, workflow IA en deux étapes, prompts additifs ;
- `docs/ARCHITECTURAL_SURVEY_V01.md` — terrain qualitatif, `building_boundary`, `connects_to`, audits v2.9/v3.0 ;
- `frontend/brickhouse-survey-to-scene-prompt.txt` — collection terrain canonique `terrain.profiles`, avec `terrain.kind:"facade_grade_profiles"` conservé ;
- `tests/test_scene_prompt_terrain_contract.py` — régression terrain ;
- `tests/test_ai_handoff_index.py` — régression de l’index de continuité ;
- issue #274 / BH-090 — dernier état du round-trip réel.

## 3. Décisions durables

Les décisions durables ont été placées dans `docs/DECISIONS.md` ou les contrats spécialisés. Les détails temporaires de benchmark/reprise sont dans `docs/CURRENT_PROJECT_STATE.md`. Aucun choix structurant nécessaire à la reprise n’est volontairement laissé seulement dans l’historique du chat.

## 4. Régressions couvertes

- terrain qualitatif Photos → Survey : tests de #304 ;
- complétude topologique Photos → Survey : tests de #305 ;
- `terrain.profiles` vs `terrain.kind:"facade_grade_profiles"` : test dédié ;
- présence/référencement du point d’entrée IA : test dédié ;
- CI complète de #306 puis CI complète de `main` après merge : vertes.

## 5. Contradictions traitées

- README M0 présenté comme état global : aligné sur le produit actuel ;
- ancien `HANDOFF.md` présenté comme point d’entrée courant : archivé et remplacé par un pointeur ;
- `NEXT_CONVERSATION.md` ancien : actualisé ;
- architecture BuildingModel/M0-only et cible frontend obsolète : remise en contexte ;
- ADR historiques : conservés mais explicitement étendus ;
- prompt Survey → Scene : collection terrain corrigée vers `profiles`, discriminant `facade_grade_profiles` conservé.

## 6. État final de passation

- **FAIT ET VÉRIFIÉ** : passation #306 fusionnée ; CI/Pages de son merge vertes ; sources de continuité indexées ; #296 fermé ; #274 actualisée.
- **EN COURS** : aucune tranche fonctionnelle.
- **OUVERT** : BH-090/#274 ; trois drifts Survey à contrôler ; fidélité visuelle/physique restante.
- **BLOQUÉ** : aucun blocage technique connu.
- **PROCHAINE ÉTAPE** : contrôler automatiquement les trois drifts avant un unique nouveau run Photos → Survey.
- **À NE PAS REFAIRE** : modifier les JSON humains, coder pour le benchmark, réécrire destructivement les prompts historiques, faire passer artificiellement les tests, demander un rerun humain après chaque petit correctif.

## 7. Contrôle de reprise

Un agent sans historique de chat doit pouvoir recevoir uniquement :

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet.

Le dépôt lui fournit alors l’ordre de lecture, les sources canoniques, les décisions, l’état vérifié, les travaux ouverts et la prochaine étape. Contrôle de passation : **réussi**.
