# SurveyAudit / SurveyCorrection — état Phase 2

Date : 2026-09-01

Ce document est un addendum opérationnel à `docs/CURRENT_PROJECT_STATE.md` et `NEXT_CONVERSATION.md`. `main`, les contrats exécutables et la CI restent autoritatifs.

## Tranches fusionnées

- #319 — `SurveyAudit v0.1`, validation et prompt indépendant.
- #320 — protocole benchmark 5 photos.
- #321 — boundary HTTP de validation SurveyAudit.
- #322 — `SurveyCorrection v0.1`, candidat complet + journal de changements.
- #323 — boundary HTTP de validation SurveyCorrection.
- #324 — résultat benchmark anonymisé, ADR-014 et passation.
- #325 — scorecard benchmark exécutable.
- #326 — durcissement des scopes de mutation `lower_certainty`, `reorient` et `merge` + alignement du prompt.
- #327 — anti-inflation du rappel : un TP d'un gold set complet doit pointer exactement une anomalie gold et les doublons de détection doivent être `DUP`.
- #328 — préflight déterministe d'éligibilité à la correction automatique.
- #329 — scope déterministe minimal de ré-audit post-correction.
- #330 — contrat et prompt `SurveyCorrectionReaudit v0.1`, diagnostiques et bornés.

## Surface automatique SurveyCorrection v0.1

Les findings `warning|error` ne sont pas tous automatiquement corrigeables.

- `add` : automatique seulement sur une cible Survey/observation/relation compatible avec un ajout explicite.
- `remove` : automatique seulement pour observation/relation.
- `lower_certainty` : automatique seulement pour observation/relation ; doit strictement diminuer au moins une certitude sans modifier le contenu sémantique ni augmenter une autre certitude.
- `reorient` : automatique seulement pour une observation ; seules la façade et les informations de rang/orientation autorisées peuvent changer, avec le wording d'orientation nécessaire.
- `merge` : manuel en v0.1.
- `reorient` d'une relation : manuel en v0.1.
- `keep`, `review`, cible `photo` et findings `info` : diagnostiques/non automatiques.

`automatic_survey_correction_finding_ids_v01()` et `survey_correction_eligibility_v01()` exposent cette décision sans lancer de passe IA.

## Ré-audit ciblé

`build_survey_correction_reaudit_scope()` construit un voisinage borné à partir d'une correction : objets modifiés, relations directement incidentes et photos déjà citées par ces objets dans l'original ou le candidat.

`SurveyCorrectionReaudit v0.1` vérifie ensuite exactement les `correction_change_ids` de la correction. Les findings sont limités aux observations/relations encore présentes dans le candidat et aux photos du scope. Une découverte hors scope doit déclencher un nouveau SurveyAudit indépendant, pas élargir silencieusement la boucle locale.

Le ré-audit ne produit jamais une seconde correction et n'adopte jamais le candidat.

## Benchmark

Le résultat historique 5 photos reste un **GO candidat** pour expérimentation contrôlée : 12/13 findings jugés soutenus, précision/actionable precision/evidence precision observées à 0,923, duplicate rate 0, avec au moins deux gains non redondants clairement démontrés (toiture omise et relation `platform supports building-envelope` non soutenue).

La clôture formelle reste volontairement ouverte. Le scorecard exécutable refuse désormais de calculer rappel/F1 si `gold_set_complete` n'est pas explicitement vrai, exige qu'un gold set complet comptabilise chaque anomalie comme détectée ou manquée dans chaque run, et empêche plusieurs TP du même run de gonfler artificiellement une même anomalie gold.

## Point où une nouvelle intervention humaine devient réellement utile

La prochaine information qui ne peut pas être fabriquée par le code est un benchmark formel reproductible :

1. même Survey source gelé et mêmes photos/PDF ;
2. au moins trois nouveaux audits indépendants dont les JSON bruts sont conservés ;
3. replay de chaque JSON sans retouche via `/api/v1/validate-survey-audit` ;
4. annotation gold exhaustive indépendante des sorties ;
5. score via le scorecard exécutable ;
6. si les seuils GO restent satisfaits, une première correction expérimentale limitée aux findings déclarés automatiquement éligibles ;
7. validation SurveyCorrection puis `SurveyCorrectionReaudit` ciblé ;
8. aucune vérité utilisateur ni claim hors scope ne doit dériver.

Tant que ces nouvelles sorties indépendantes ne sont pas disponibles, il ne faut pas présenter le benchmark comme formellement clos.

## HOLD

`SceneAudit` reste **HOLD**. Aucun gain spécifique au-dessus de `validate-scene-against-survey` n'a été mesuré.
