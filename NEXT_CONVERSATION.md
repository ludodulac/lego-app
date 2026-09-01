# Boldüngo / BrickHouse — reprise immédiate

Date : 2026-09-01

## À lire dans cet ordre

1. `AI_START_HERE.md`
2. `README.md`
3. `docs/CURRENT_PROJECT_STATE.md`
4. `docs/ARCHITECTURE.md` et `docs/DECISIONS.md`
5. `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` si la tâche concerne l’évolution du pipeline IA
6. les contrats spécialisés concernés par la tâche
7. `HANDOFF.md` seulement pour l’historique utile

Toujours vérifier l’état réel de `main`, des PR/issues, de la CI et de Pages avant d’agir. `main` et les tests exécutables priment sur cette passation.

## NOUVELLE ÉTUDE PRIORITAIRE — AUDITS IA INDÉPENDANTS

Une étude architecturale complète a été ajoutée dans `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` après inspection de l’état réel du pipeline, des contrats Survey/Scene, des validateurs backend, de l’API, des tests et de la documentation.

Conclusion actuelle :
- **SurveyAudit indépendant : GO expérimental**, additif, après validation déterministe du Survey ;
- **SceneAudit : GO conditionnel**, à activer seulement si les mesures démontrent qu’il détecte des anomalies photo-géométrie non déjà couvertes par `validate-scene-against-survey` ;
- aucun audit ne doit modifier silencieusement Survey ou Scene ;
- les validateurs existants restent obligatoires ;
- les boucles supplémentaires ne sont déclenchées que lorsqu’un finding actionnable existe ;
- le benchmark 5 photos doit mesurer précision/recall, doublons, identité multi-vues, calibration des certitudes, relations, dérive géométrique et gain net de l’audit.

Pour reprendre cette évolution, commencer par `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` avant toute implémentation.

## FAIT ET VÉRIFIÉ

- PR #308 : contrat sémantique de direction de pente terrain clarifié.
- PR #309 : audit de couverture Survey v3.1 ajouté (roof, building boundary, root `id`, etc.).
- PR #310 : cache-buster du package Survey corrigé.
- PR #311 : handoff Survey → Scene verrouillé sur le Survey actif validé ; l’état Survey/Scene obsolète est invalidé avant un nouvel import.
- Le shell Boldüngo a depuis été rendu numéroté et les garde-fous Survey ont encore été renforcés sur `main`; toujours vérifier le SHA réel avant reprise.
- Issue pipeline : #274 / BH-090.
- Issue UX : #312.

## DÉCISION PRODUIT DURABLE — INTERFACE UNIQUE

Boldüngo doit rester une application à UNE SEULE PAGE / UN SEUL ÉCRAN PRINCIPAL. Le parcours normal utilise les états du même shell applicatif : navigation basse persistante, progression visible, actions principales accessibles au pouce, faible profondeur et pas de long scroll pour le parcours principal.

## ÉTAT DU BENCHMARK

Le benchmark principal reste la maison réelle à 5 photos et largeur de façade avant 10 m. Il sert à révéler des défauts génériques, jamais à hardcoder cette maison.

Les garde-fous Photos → Survey ont été renforcés pour l’identité physique, le terrain, la topologie, la couverture, le contrat final et le raisonnement multi-vues. Ne pas corriger manuellement un JSON utilisateur pour le faire passer.

## PROCHAINE ACTION HUMAINE

Ne demander un nouveau run humain qu’à un jalon utile. Pour l’étude des audits indépendants, aucune nouvelle génération utilisateur n’est nécessaire avant d’avoir au minimum défini et testé le contrat `SurveyAudit v0.1` de façon additive.

## À NE PAS REFAIRE

- ne pas renommer mécaniquement BrickHouse en Boldüngo ;
- ne pas modifier un JSON utilisateur pour le faire passer ;
- ne pas affaiblir les validateurs ;
- ne pas hardcoder la maison benchmark ;
- ne pas demander à l’utilisateur du travail GitHub/technique réalisable par l’agent ;
- ne pas demander un test humain après chaque micro-correctif ;
- ne pas remplacer les validations déterministes par un vote IA ;
- ne pas laisser un auditeur réécrire directement la source qu’il contrôle.

## Instruction suffisante pour repartir

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main`, puis lis `docs/AI_INDEPENDENT_AUDITS_PROPOSAL.md` et reprends l’étude/implémentation additive des audits IA indépendants sans remplacer le pipeline existant.
