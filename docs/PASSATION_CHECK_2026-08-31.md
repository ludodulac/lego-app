# Contrôle de passation — 2026-08-31

Ce fichier matérialise le contrôle demandé par `AI_START_HERE.md`. Il peut rester comme trace d’audit ; l’état vivant reste `docs/CURRENT_PROJECT_STATE.md`.

## 1. Main / PR / CI / déploiement

- Point de départ vérifié : `main` = `62655f6e1bd33c3ea469fe10af2ada27c586a889` (PR #305).
- CI de ce point : succès, run 1257.
- GitHub Pages de ce point : succès, run 514.
- PR historique #296 contient une première version de `AI_START_HERE.md` mais est devenue non-mergeable/stale ; la présente branche la remplace proprement sur le `main` courant.
- La présente passation doit être fusionnée uniquement après CI verte, puis `main` et Pages doivent être revérifiés.

## 2. Inventaire de cette tranche

Ajouts/mises à jour :
- `AI_START_HERE.md` — point d’entrée et protocole canonique ;
- `README.md` — pipeline produit actuel ;
- `NEXT_CONVERSATION.md` — reprise immédiate actuelle ;
- `HANDOFF.md` — pointeur non contradictoire vers la continuité courante ;
- `docs/HANDOFF_HISTORY_2026-08-23.md` — conservation de l’ancien contexte utile ;
- `docs/CURRENT_PROJECT_STATE.md` — état vérifié, benchmark, limites, ouverts et prochaines étapes ;
- `docs/ARCHITECTURE.md` — pipeline actuel Survey/Scene/LEGO ;
- `docs/DECISIONS.md` — ADR Survey/Scene, vérité architecturale vs LEGO, workflow manuel en deux étapes et prompts additifs ;
- `docs/ARCHITECTURAL_SURVEY_V01.md` — terrain qualitatif, `building_boundary`, `connects_to`, audits v2.9/v3.0 ;
- `frontend/brickhouse-survey-to-scene-prompt.txt` — correction de la collection terrain canonique `terrain.profiles` sans changer `terrain.kind` ;
- `tests/test_scene_prompt_terrain_contract.py` — régression du contrat terrain ;
- `tests/test_ai_handoff_index.py` — régression de l’index de continuité.

## 3. Décisions durables indexées

Les décisions durables de la conversation ont été déplacées vers `docs/DECISIONS.md` et les contrats spécialisés. Les détails temporaires du benchmark et de reprise sont dans `docs/CURRENT_PROJECT_STATE.md`.

## 4. Régressions couvertes

- terrain qualitatif Photos → Survey : tests existants de #304 ;
- complétude topologique Photos → Survey : tests existants de #305 ;
- `terrain.profiles` vs `terrain.kind:"facade_grade_profiles"` : nouveau test dédié ;
- présence/référencement du point d’entrée IA : nouveau test dédié.

## 5. Références obsolètes/contradictoires traitées

- README M0 présenté comme état global : remplacé par le pipeline actuel ;
- `HANDOFF.md` ancien présenté comme « à lire en premier » : converti en pointeur, historique conservé ;
- `NEXT_CONVERSATION.md` arrêté au 29/08 : remplacé par la reprise du 31/08 ;
- `docs/ARCHITECTURE.md` centré uniquement sur BuildingModel/M0 et Next.js cible : aligné sur l’implémentation actuelle ;
- ADR-003/004/005 historiques : explicitement marqués/étendus sans effacer leur historique ;
- prompt Survey → Scene : `Terrain utilise facade_grade_profiles` corrigé en collection `profiles`, tout en conservant le discriminant `terrain.kind:"facade_grade_profiles"`.

## 6. État indexé

- **FAIT ET VÉRIFIÉ** : voir `docs/CURRENT_PROJECT_STATE.md`.
- **EN COURS** : uniquement la fusion/validation de cette passation.
- **OUVERT** : BH-090/#274, trois drifts de Survey à contrôler, fidélité visuelle/physique restante.
- **BLOQUÉ** : aucun blocage technique connu.
- **PROCHAINE ÉTAPE** : contrôles automatiques des drifts avant un unique nouveau run Photos → Survey.
- **À NE PAS REFAIRE** : modifier les JSON humains, coder pour le benchmark, réécrire destructivement les prompts historiques, faire passer artificiellement les tests, solliciter l’utilisateur entre petites étapes.

## 7. Test de reprise mentale

Un agent sans historique de chat doit pouvoir recevoir uniquement :

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet.

Il y trouvera l’ordre de lecture, les sources canoniques, l’état vérifié, les décisions, les ouverts et la prochaine étape. Si la PR de passation est fusionnée avec CI/Pages vertes, le contrôle est considéré réussi.
