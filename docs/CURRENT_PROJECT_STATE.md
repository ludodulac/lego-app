# Boldüngo / BrickHouse — état courant vérifié

Date de passation : 2026-09-01

Ce document est l’index opérationnel du travail récent. Il complète `AI_START_HERE.md`; `main` et les tests exécutables restent la source technique de vérité. Toujours revérifier les SHA, PR, CI et déploiements au début d’une nouvelle conversation.

## FAIT ET VÉRIFIÉ

### État Git récent

Dernier `main` vérifié au moment de cette passation : `ed8de59537dc74474c2de27a5f93017bb4a4025f`, merge de la PR #323.

Tranches indépendantes récemment fusionnées :

- #319 — `SurveyAudit v0.1`, validateur Python, prompt indépendant, tests et ADR-013 ;
- #320 — protocole/scorecard du benchmark SurveyAudit 5 photos ;
- #321 — boundary HTTP `POST /api/v1/validate-survey-audit` ;
- #322 — `SurveyCorrection v0.1`, journal de changements, gel des vérités utilisateur, prompt de correction explicite ;
- #323 — boundary HTTP `POST /api/v1/validate-survey-correction`.

CI vérifiée :

- PR #322 : 771 tests Python verts ; LEGO Geometry Engine 26 verts / 2 skipped ; tous les gardes/smokes frontend, handoff et pipelines verts ;
- PR #323 : 774 tests Python verts ; LEGO Geometry Engine 26 verts / 2 skipped ; tous les gardes/smokes frontend, handoff et pipelines verts.

### Pipeline architectural de référence

Le principe durable reste :

`PHOTOS → ArchitecturalSurvey → ArchitecturalScene → construction LEGO → validation physique LEGO → modèle`

Responsabilités :

- `ArchitecturalSurvey v0.1` = autorité sémantique/observée ;
- `ArchitecturalScene v0.2` = autorité métrique/géométrique ;
- les contraintes LEGO ne réécrivent jamais silencieusement la vérité architecturale ;
- `SurveyAudit` ajoute un diagnostic visuel après validation déterministe ;
- `SurveyCorrection` propose un candidat séparé, traçable et revalidé ; le Survey source reste intact.

Voir `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md`, `docs/DECISIONS.md` et `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md`.

### SurveyAudit v0.1

`backend/brickhouse/survey/audit.py` définit le contrat indépendant. Les findings portent une cible, un statut, une sévérité, une action suggérée et des preuves photo. L’audit ne modifie jamais le Survey.

Le boundary `/api/v1/validate-survey-audit` impose d’abord la validation déterministe du Survey, puis vérifie le SurveyAudit. Il retourne l’audit parsé, les issues, `valid` et `needs_correction` ; il ne corrige rien.

Prompt dédié : `frontend/brickhouse-survey-independent-audit-v01.txt`.

### SurveyCorrection v0.1

`backend/brickhouse/survey/correction.py` définit un artefact séparé contenant :

- un Survey candidat complet ;
- un journal `changes[]` ;
- pour chaque mutation, un lien vers un `finding_id` actionnable et la même `suggested_action`.

En v0.1, `name`, `canonical_frame`, photos/métadonnées, `known_measurements`, `representation_policy` et `notes` sont gelés. Les actions `keep`/`review` ne peuvent pas muter directement le Survey. Toute addition/suppression/modification non déclarée est rejetée. Le candidat repasse les validateurs Survey et le roof guard.

Le boundary `/api/v1/validate-survey-correction` valide successivement le Survey original, le SurveyAudit puis le SurveyCorrection. Il retourne `valid_for_reaudit` mais n’adopte pas le candidat.

Prompt dédié : `frontend/brickhouse-survey-correction-v01.txt`.

## BENCHMARK SURVEYAUDIT — MAISON RÉELLE 5 PHOTOS

Le benchmark principal reste la maison réelle à 5 photos avec largeur avant utilisateur de 10 m. Les photos, le PDF et le Survey utilisateur sont privés et ne doivent pas être copiés dans le dépôt sans décision explicite.

Trois audits indépendants ont été collectés sur le même Survey intact : 4, 3 et 6 findings ; les trois ont conclu `needs_correction`.

Adjudication actuelle : 12 findings sur 13 visuellement soutenus/utiles ; 1 faux positif clair sur l’identité multi-vues d’une fenêtre haute. Mesures directement établies : précision/actionable precision = 0,923 ; evidence precision = 0,923 ; duplicate rate = 0 ; correction trigger rate = 1,0. Au moins deux gains visuels nouveaux sont démontrés au-delà du JSON seul : toiture visible totalement omise et relation `platform supports building-envelope` non soutenue visuellement.

Le résultat est **GO candidat pour expérimentation contrôlée**, pas encore clôture formelle du benchmark. Les sorties historiques n’ont pas été persistées comme fichiers puis rejouées byte-for-byte dans le boundary ajouté ensuite. De plus, rappel/F1 et rappels par catégorie exigent un gold set exhaustif indépendant des sorties des auditeurs.

Voir `docs/SURVEY_AUDIT_BENCHMARK_V01.md` et `docs/SURVEY_AUDIT_BENCHMARK_RESULT_2026-09-01.md`.

## ROUND-TRIP MANUEL / BH-090

L’issue #274 / BH-090 reste le jalon bout-en-bout. Le workflow manuel principal reste volontairement en deux étapes :

1. Photos → Survey ;
2. Survey validé + PDF original → Scene.

Le flux historique `external-bundle-0.1` reste une compatibilité, pas le workflow principal. Les nouveaux audits/corrections s’insèrent entre Survey et Scene sans fusionner les contrats.

## MOTEUR GÉOMÉTRIQUE LEGO

Le sous-package `lego_geometry_engine/` reste intégré via `backend/brickhouse/bricks/geometry_adapter.py`.

Capacités : triangles LDraw transformés, broad phase AABB, collision/contact narrow phase, ray-casting de containment, topologie de support et connecteurs exacts pour distinguer contact légal/collision.

Limites connues : pas encore de modèle général complet pour Technic, clips, charnières, SNOT, contraintes mécaniques, stress ou stabilité globale.

## CONTRATS PROMPT À PRÉSERVER

Photos → Survey : conserver le prompt historique et ses couches additives terrain/topologie/final-contract. Ne pas condenser une règle nouvelle en supprimant des garde-fous existants.

Survey → Scene : handoff v4.3 ; Survey autorité sémantique ; PDF original preuve géométrique supplémentaire ; `terrain.profiles` collection canonique ; une primitive certaine ne disparaît pas seulement parce que sa métrique est difficile.

SurveyAudit : auditeur indépendant, diagnostic uniquement, preuves photo obligatoires sauf `insufficient_evidence`, aucune réécriture du Survey.

SurveyCorrection : candidat séparé, changements explicitement journalés, aucune vérité utilisateur modifiée, aucun opportunistic cleanup, validation déterministe obligatoire.

## OUVERT

### Clôture formelle du benchmark SurveyAudit

Il manque encore :

1. conservation d’un triplet brut de sorties d’audit ;
2. replay exact sans retouche via `/api/v1/validate-survey-audit` ;
3. gold set exhaustif pour rappel/F1 et rappels par catégorie ;
4. expérimentation d’une correction sur candidat et vérification qu’elle n’introduit aucune dérive non ciblée.

### Durcissement SurveyCorrection

Le contrat v0.1 protège déjà les champs Survey globaux et les mutations non déclarées, mais les actions qui modifient un objet existant doivent encore être évaluées finement. Une action déclarée `lower_certainty`, `reorient` ou `merge` ne doit pas servir de couverture à des changements sans rapport dans le même objet. Ajouter des invariants ciblés/tests négatifs avant de confier un benchmark privé au correcteur.

### Ré-audit ciblé

`valid_for_reaudit` existe, mais aucun contrat dédié de ré-audit ciblé n’est encore défini. La prochaine boucle doit contrôler uniquement les findings appliqués et les régressions possibles, avec nombre d’itérations borné ; ne pas créer une boucle IA ouverte.

### Fidélité visuelle / physique restante

Après stabilisation du round-trip : fenêtres encore schématiques ; cadres/retraits/appuis/linteaux partiels ; terrasse et escalier approximatifs ; position de cheminée prudente/estimée ; terrain/rue/trottoir incomplets dans le rendu final. Ne jamais inventer des dimensions architecturales pour améliorer l’apparence.

## HOLD

### SceneAudit

**HOLD.** Aucun benchmark n’a encore démontré un gain propre de SceneAudit au-dessus de `validate-scene-against-survey`. Ne pas l’implémenter par symétrie avec SurveyAudit.

## PROCHAINE ÉTAPE

1. Fermer la documentation du benchmark/ADR-014 et garder la passation synchronisée avec `main`.
2. Durcir les mutations in-place/merge de SurveyCorrection avec tests négatifs.
3. Définir un mécanisme minimal de ré-audit ciblé, borné et non-mutant.
4. Préparer une persistance/scoring reproductible des runs sans publier les assets privés.
5. N’appeler l’utilisateur que lorsqu’un nouveau triplet brut ou une validation visuelle humaine apporte une information impossible à obtenir autrement.

## À NE PAS REFAIRE

- ne pas modifier un JSON utilisateur pour le faire passer ;
- ne pas affaiblir un validateur pour accepter une sortie IA incorrecte ;
- ne pas hardcoder la maison benchmark ;
- ne pas demander un run humain après chaque micro-correctif ;
- ne pas compter plusieurs passes dans le même contexte comme audits indépendants ;
- ne pas publier rappel/F1 sans gold set exhaustif ;
- ne pas laisser SurveyAudit ou SurveyCorrection réécrire silencieusement la source ;
- ne pas laisser les contraintes LEGO modifier la Scene ;
- ne pas publier les photos/PDF/Survey privés sans décision explicite ;
- ne pas lancer SceneAudit sans mesure de gain non redondant.

## Validation de reprise

Une nouvelle conversation doit pouvoir commencer par :

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main`, puis lis `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md`, `docs/SURVEY_AUDIT_BENCHMARK_RESULT_2026-09-01.md` et reprends la boucle explicite SurveyAudit → SurveyCorrection → validation → ré-audit ciblé.
