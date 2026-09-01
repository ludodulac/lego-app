# Boldüngo / BrickHouse — reprise immédiate

Date : 2026-09-01

## À lire dans cet ordre

1. `AI_START_HERE.md`
2. `README.md`
3. `docs/CURRENT_PROJECT_STATE.md`
4. `docs/ARCHITECTURE.md` et `docs/DECISIONS.md`
5. `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` pour l’évolution du pipeline IA
6. `backend/brickhouse/survey/audit.py`
7. les contrats spécialisés concernés par la tâche
8. `HANDOFF.md` seulement pour l’historique utile

Toujours vérifier l’état réel de `main`, des PR/issues, de la CI et de Pages avant d’agir. `main` et les tests exécutables priment sur cette passation.

## PRIORITÉ — AUDITS IA INDÉPENDANTS

La Phase 1 de `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` a commencé de façon additive.

### FAIT ET VÉRIFIÉ

- PR #319 fusionnée sur `main` : `SurveyAudit v0.1` existe comme contrat Pydantic séparé dans `backend/brickhouse/survey/audit.py`.
- Le contrat expose des findings structurés, une preuve photo, des cibles Survey, une sévérité, une action suggérée et un statut global.
- Un finding non `insufficient_evidence` doit citer une preuve photo.
- `validate_survey_audit()` vérifie notamment l’identité du Survey audité, les références photo/observation/relation, les IDs de findings et la cohérence `pass|needs_correction`.
- `frontend/brickhouse-survey-independent-audit-v01.txt` définit une passe indépendante strictement diagnostique : elle ne doit jamais retourner un Survey corrigé.
- `tests/survey/test_survey_audit.py` couvre contrat, validation, non-mutation, preuve, statut, schéma JSON et prompt.
- ADR-013 documente la frontière durable : un audit IA indépendant est un diagnostic séparé, jamais une mutation.
- La PR #319 a aussi réparé deux régressions déjà présentes sur `main` : garde-fous texte supprimés du final-contract Survey v3.3 et garde CI du shell devenu obsolète par rapport au câblage réel.
- CI PR #1330 : entièrement verte après correction ; suite principale 763 tests verts, LEGO Geometry Engine 26 verts / 2 skipped, puis tous les smoke/gardes frontend verts.

### EN COURS

Aucune correction automatique Survey n’est implémentée. Le nouveau contrat est volontairement importable/validable côté Python mais n’est pas encore intégré au parcours produit ni à une boucle de correction.

### PROCHAINE ÉTAPE

Poursuivre la **Phase 1 avant de passer à la Phase 2** :
1. décider le point d’import/validation HTTP minimal pour un `SurveyAudit v0.1` sans l’intégrer encore au workflow utilisateur ;
2. ajouter ce boundary API si cela reste cohérent avec les patterns existants ;
3. créer/figer une fiche de scoring benchmark 5 photos sans publier les photos privées ;
4. définir les métriques automatisables du Survey initial vs audit/correction ;
5. seulement ensuite préparer le workflow explicite de correction Survey (Phase 2), avec journal de modifications et validation que chaque changement est relié à un finding.

Ne pas lancer `SceneAudit` en production avant mesure du gain spécifique de `SurveyAudit`.

## DÉCISIONS À PRÉSERVER

- **SurveyAudit indépendant : GO expérimental**, après validation déterministe du Survey.
- **SceneAudit : GO conditionnel**, uniquement si les mesures montrent des anomalies photo-géométrie non couvertes par `validate-scene-against-survey`.
- aucun audit ne remplace les validateurs déterministes ;
- aucun audit ne modifie silencieusement Survey ou Scene ;
- aucune absence de preuve ne devient preuve d’absence ;
- une boucle de correction future doit être explicite, traçable et limitée ;
- aucune règle ne doit hardcoder la maison benchmark.

## ÉTAT DU BENCHMARK

Le benchmark principal reste la maison réelle à 5 photos et largeur de façade avant 10 m. Il sert à révéler des défauts génériques. Les photos privées ne doivent pas être ajoutées au dépôt sans décision explicite.

Aucune nouvelle génération humaine n’est requise simplement parce que le contrat `SurveyAudit v0.1` existe. Le prochain run humain doit correspondre à un jalon de mesure utile.

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
- ne pas réintroduire les deux régressions réparées par #319 dans le final-contract Survey ou le garde CI du shell.

## Instruction suffisante pour repartir

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main`, puis lis `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` et reprends à partir de `SurveyAudit v0.1` en restant strictement additif.
