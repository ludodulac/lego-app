# Boldüngo / BrickHouse — reprise immédiate

Date : 2026-09-01

## À lire dans cet ordre

1. `AI_START_HERE.md`
2. `README.md`
3. `docs/CURRENT_PROJECT_STATE.md`
4. `docs/ARCHITECTURE.md` et `docs/DECISIONS.md`
5. `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md`
6. `docs/SURVEY_AUDIT_BENCHMARK_V01.md`
7. `docs/SURVEY_AUDIT_BENCHMARK_RESULT_2026-09-01.md`
8. `backend/brickhouse/survey/audit.py` et `backend/brickhouse/survey/correction.py`
9. les contrats spécialisés concernés par la tâche
10. `HANDOFF.md` seulement pour l’historique utile

Toujours vérifier l’état réel de `main`, des PR/issues, de la CI et de Pages avant d’agir. `main` et les tests exécutables priment sur cette passation.

## PRIORITÉ — BOUCLE SURVEY AUDIT / CORRECTION EXPÉRIMENTALE

La proposition d’audits IA indépendants a désormais franchi les fondations de Phase 1 et la première infrastructure de Phase 2.

### FAIT ET VÉRIFIÉ

- PR #319 : `SurveyAudit v0.1`, validateur Python, prompt indépendant et ADR-013.
- PR #320 : protocole et scorecard du benchmark 5 photos dans `docs/SURVEY_AUDIT_BENCHMARK_V01.md`.
- PR #321 : boundary HTTP `POST /api/v1/validate-survey-audit`, strictement diagnostique et précédé de la validation déterministe du Survey.
- Benchmark humain : 3 runs indépendants, respectivement 4 / 3 / 6 findings, tous `needs_correction` ; 12 findings sur 13 jugés visuellement soutenus ; précision/actionable precision et evidence precision observées à 0,923 ; duplicate rate 0 ; correction trigger 1,0.
- Le benchmark démontre au moins deux gains visuels non décidables par le JSON seul : toiture visible totalement omise et relation `platform supports building-envelope` non soutenue par les photos.
- Le rappel/F1 et les rappels par catégorie ne sont pas encore publiables honnêtement : il manque une annotation gold exhaustive indépendante des sorties d’audit.
- Les trois sorties historiques ont été revues par inspection contre le contrat, mais n’ont pas été persistées comme fichiers puis rejouées byte-for-byte dans le boundary ajouté ensuite. Le résultat est donc **GO candidat**, pas encore clôture formelle de tous les critères du benchmark.
- PR #322 : `SurveyCorrection v0.1`, journal de changements lié aux findings, gel des vérités utilisateur/métadonnées, prompt de correction explicite, ADR-014 en préparation documentaire.
- PR #323 : boundary HTTP `POST /api/v1/validate-survey-correction` ; valide successivement Survey source, SurveyAudit source puis SurveyCorrection ; retourne seulement l’éligibilité au ré-audit, sans adoption automatique du candidat.
- CI PR #322 : 771 tests Python verts, LEGO Geometry Engine 26 verts / 2 skipped, tous les gardes/smokes frontend et pipelines verts.
- CI PR #323 : 774 tests Python verts, LEGO Geometry Engine 26 verts / 2 skipped, tous les gardes/smokes frontend et pipelines verts.

Au point de cette passation, le dernier `main` vérifié après #323 est `ed8de59537dc74474c2de27a5f93017bb4a4025f`. Toujours le revérifier avant d’agir.

## INVARIANTS DU WORKFLOW DE CORRECTION

- Le Survey source ne doit jamais être modifié silencieusement.
- `SurveyCorrection` transporte un candidat complet et un journal explicite des mutations.
- Chaque mutation doit être reliée à un finding actionnable validé et utiliser la même `suggested_action`.
- `keep` et `review` ne peuvent pas déclencher une mutation directe.
- En v0.1, `name`, `canonical_frame`, photos/métadonnées, `known_measurements`, `representation_policy` et `notes` sont gelés.
- Toute modification non déclarée d’une observation/relation fait échouer la correction.
- Le candidat doit encore passer les validateurs Survey déterministes et les guards de toiture.
- Le boundary de correction ne publie ni n’adopte automatiquement le candidat ; il dit seulement s’il est valide pour un contrôle ciblé suivant.

## PROCHAINE ÉTAPE

Poursuivre sans redemander de travail humain tant que ce n’est pas nécessaire :

1. fusionner/valider la tranche documentaire du benchmark et ADR-014 ;
2. durcir `SurveyCorrection` là où une action déclarée pourrait encore masquer une modification trop large d’un objet existant, notamment `lower_certainty`, `reorient` et `merge`, avec tests négatifs avant utilisation sur le benchmark privé ;
3. définir un ré-audit **ciblé** minimal qui contrôle uniquement les changements appliqués et les régressions qu’ils peuvent induire, au lieu de lancer une boucle IA illimitée ;
4. préparer un artefact de scoring reproductible qui peut conserver résultats/validation sans publier les photos privées ;
5. pour la clôture formelle du benchmark, conserver un nouveau triplet brut de SurveyAudit (ou les trois historiques s’ils sont récupérables), les passer sans retouche par `/api/v1/validate-survey-audit`, puis établir une annotation gold exhaustive avant de publier rappel/F1 ;
6. seulement après cette mesure, exécuter une correction expérimentale sur le Survey privé et vérifier qu’aucune vérité utilisateur ni claim non ciblé n’a dérivé.

## DÉCISIONS À PRÉSERVER

- **SurveyAudit : GO candidat pour expérimentation contrôlée**, après validation déterministe du Survey.
- **SurveyCorrection : expérimental et explicite**, jamais une réécriture silencieuse.
- **SceneAudit : HOLD**, tant qu’un gain non redondant au-dessus de `validate-scene-against-survey` n’est pas mesuré.
- aucun audit ne remplace les validateurs déterministes ;
- aucune absence de preuve ne devient preuve d’absence ;
- aucune vérité `user_provided` ne change automatiquement ;
- aucune règle ne doit hardcoder la maison benchmark ;
- les photos/PDF/Survey privés ne sont pas ajoutés au dépôt sans décision explicite.

## AUTRES REPÈRES

- Issue pipeline : #274 / BH-090.
- Issue UX : #312.
- Boldüngo reste une application à UNE SEULE PAGE / UN SEUL ÉCRAN PRINCIPAL.
- Ne pas renommer mécaniquement BrickHouse en Boldüngo.

## À NE PAS REFAIRE

- ne pas modifier un JSON utilisateur pour le faire passer ;
- ne pas affaiblir les validateurs ;
- ne pas hardcoder la maison benchmark ;
- ne pas demander à l’utilisateur du travail GitHub/technique réalisable par l’agent ;
- ne pas demander un test humain après chaque micro-correctif ;
- ne pas remplacer les validations déterministes par un vote IA ;
- ne pas laisser un auditeur réécrire directement la source qu’il contrôle ;
- ne pas faire trois pseudo-runs dans un même contexte et les compter comme indépendants ;
- ne pas publier rappel/F1 sans gold set exhaustif ;
- ne pas lancer SceneAudit par symétrie avec SurveyAudit.

## Instruction suffisante pour repartir

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main`, puis lis `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md`, `docs/SURVEY_AUDIT_BENCHMARK_RESULT_2026-09-01.md` et reprends à partir de la boucle explicite `SurveyAudit -> SurveyCorrection -> validation -> ré-audit ciblé` en restant strictement additif.

## MISE À JOUR — fin de tranche Phase 2 du 2026-09-01

Les étapes techniques 1 à 4 ci-dessus ont depuis été largement réalisées. Lire aussi `docs/SURVEY_AUDIT_CORRECTION_PHASE2_STATUS.md` avant d’agir.

Tranches supplémentaires fusionnées sur `main` :
- #324 — résultat benchmark anonymisé + ADR-014/passation ;
- #325 — scorecard benchmark exécutable ;
- #326 — scopes `lower_certainty` / `reorient` durcis, `merge` et reorient relation rendus manuels en v0.1, prompt aligné ;
- #327 — protection du gold scorecard contre l’inflation du rappel ;
- #328 — préflight déterministe d’éligibilité des findings à une correction automatique ;
- #329 — calcul du scope minimal de ré-audit post-correction ;
- #330 — `SurveyCorrectionReaudit v0.1` + validateur + prompt borné, diagnostique seulement.

Le prochain travail qui apporte réellement une nouvelle information nécessite désormais des sorties humaines/indépendantes : conserver au moins trois nouveaux SurveyAudit JSON bruts sur le même Survey/photos gelés, les rejouer sans retouche par le boundary, puis produire un gold set exhaustif indépendant. Le scorecard peut alors calculer rappel/F1 honnêtement. Si les seuils GO restent satisfaits, seulement ensuite exécuter une première correction privée limitée aux findings déclarés automatiquement éligibles, la valider puis lancer le ré-audit ciblé.

`SceneAudit` reste **HOLD**.
