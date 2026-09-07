# AI START HERE — Boldüngo / BrickHouse

Ce fichier est le point d’entrée obligatoire de tout agent IA qui reprend ce dépôt. Il ne décrit volontairement pas l’état technique du jour : il explique comment le reconstruire depuis les sources réelles et comment reprendre sans repartir de zéro.

## PROMPT OFFICIEL À COPIER DANS UNE NOUVELLE CONVERSATION

> Va dans le dépôt `ludodulac/lego-app`.
> Lis `AI_START_HERE.md` et suis exactement sa procédure de reprise.
> Vérifie l’état réel de `main`, des PR/issues et de la CI avant d’agir.
> Reprends ensuite le chantier prioritaire indiqué par le dépôt.
> Ne repars pas de zéro et préserve l’existant.

Compatibilité historique : `Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet.` reste une instruction courte valide, mais le bloc ci-dessus est désormais le prompt recommandé.

Ce prompt doit rester valable même si la passation date de plusieurs semaines. Si une vieille passation, un ancien prompt ou une conversation contredit l’état technique actuel du dépôt, **l’état actuel du dépôt gagne**. Les principes et ADR restent normatifs ; les SHA, PR, CI, tests, endpoints et fonctionnalités doivent être revérifiés.

## 1. Reprise rapide opérationnelle

Avant de lire largement le dépôt, reconstruire seulement ce qui est nécessaire pour agir :

1. **État réel** — lire le HEAD de `main`, les PR ouvertes et les derniers checks/CI pertinents. Ne jamais prendre un SHA ou un statut recopié dans une passation comme vérité actuelle.
2. **Priorité** — lire la section de reprise de `PROGRESSION.md`, puis confirmer le chantier dans les PR/issues et le code actuels.
3. **Zone** — identifier la frontière du pipeline touchée, puis utiliser la table ci-dessous pour ne lire que les contrats/modules/tests concernés.
4. **Garde-fous** — relire les invariants sentinelles ci-dessous et leur source canonique avant de modifier le code.
5. **Validation** — choisir FAST pendant l'itération, TARGETED pour la couche et ses frontières, FULL avant fusion ou dès que le risque traverse plusieurs couches.
6. **Terminé** — modification minimale, tests ciblés verts, invariants concernés préservés, régression ajoutée si bug, FULL/CI verte lorsque requise, et `PROGRESSION.md` mis à jour seulement si le point de reprise change.

### Routage par zone

| Zone touchée | Lire d'abord | Code/tests à inspecter en priorité |
| --- | --- | --- |
| Photos → Survey | `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_SURVEY_V01.md`, puis `docs/ARCHITECTURAL_REASONING_PASS.md` si raisonnement multi-vues | `backend/brickhouse/survey/`, `tests/survey/`, `tests/pipeline/test_architectural_analysis_pipeline.py` |
| Survey → Scene / géométrie architecturale | `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md` | `backend/brickhouse/scene/`, `tests/scene/`, `tests/pipeline/test_architectural_scene_candidate.py` |
| Scene → représentation LEGO / géométrie / ouvertures | `docs/ARCHITECTURAL_SCENE_V02.md`, `docs/ARCHITECTURE.md`, décisions concernées dans `docs/DECISIONS.md` | `backend/brickhouse/bricks/`, `tests/bricks/test_scene_*`, `tests/bricks/test_wall_*`, `tests/bricks/test_building_layout.py` |
| Support / validation physique / readiness | `docs/ARCHITECTURAL_SCENE_V02.md` + décisions BH-153/BH-178…BH-182 dans `docs/DECISIONS.md`/issues | `backend/brickhouse/bricks/physical_validation.py`, `scene_physical_support.py`, `scene_production_readiness.py`, `tests/bricks/test_scene_physical_*`, `test_scene_production_readiness.py` |
| BOM / AssemblyPlan / InstructionPlan / BagPlan / export | `docs/ARCHITECTURE.md` + décisions/export concernées | `backend/brickhouse/bricks/{bom,assembly,instructions,bags,export}.py`, `tests/bricks/test_{bom,assembly,instructions,bags,export}.py` |
| Viewer / parcours déployé | `README.md`, workflow CI/déploiement concerné | `frontend/`, `scripts/`, `.github/workflows/`, tests frontend et smoke/deployment existants |

N'élargir vers `docs/CURRENT_PROJECT_STATE.md`, `HANDOFF.md` ou une chronologie ancienne que si le chantier actuel exige ce contexte. Ces documents sont contextuels et peuvent vieillir ; ils ne doivent pas détourner vers une ancienne tentative.

### Invariants sentinelles

Cette liste est un index opérationnel, pas une deuxième constitution. La formulation normative reste dans `PROJECT_PRINCIPLES.md` et les contrats spécialisés.

- **Survey = autorité sémantique.** Une transformation aval ne réécrit pas silencieusement objets, identités, relations ou certitudes observées. Source : `PROJECT_PRINCIPLES.md`, `docs/ARCHITECTURAL_SURVEY_V01.md`. Protection : tests `tests/survey/` et contrats Survey→Scene.
- **Scene = autorité métrique/géométrique.** La génération LEGO peut approximer sa représentation, pas muter la Scene pour rendre le modèle constructible. Source : `PROJECT_PRINCIPLES.md`, `docs/ARCHITECTURAL_SCENE_V02.md`. Protection : `tests/scene/` + tests `tests/bricks/test_scene_*`.
- **Un inconnu reste inconnu.** Pas de mesure, coordonnée, pente, support, objet ou certitude inventé pour faire passer un pipeline. Source : principes + contrats Survey/Scene. Protection : tests de provenance/unknowns/readiness et demandes humaines minimales existantes.
- **Les pertes restent explicites.** Approximation, simplification et impossibilité de fidélité se propagent via diagnostics/provenance/`fidelity_issues` au lieu d'être masquées. Source : principes + contrats d'export. Protection : tests de fidelity/provenance/export.
- **Support physique ≠ proximité visuelle.** Lorsqu'une garantie de production est revendiquée, support/connectivité doivent être prouvés dans le périmètre déclaré ; sinon l'état reste non prouvé/bloqué. Source : décisions de validation physique. Protection : `tests/bricks/test_scene_physical_*`, readiness et validation physique.
- **Artefacts aval cohérents.** BOM, AssemblyPlan, InstructionPlan et BagPlan ne doivent pas revendiquer plus que leurs validateurs ne prouvent et doivent rester cohérents avec le BrickModel/ordre d'assemblage. Source : contrats de ces modules. Protection : leurs tests dédiés + tests d'export.
- **Préserver avant de remplacer.** Une optimisation de workflow ne supprime aucune capacité métier existante et une correction vise la cause générique avec régression quand elle peut revenir. Source : `PROJECT_PRINCIPLES.md`.

### Niveaux de validation

Ces niveaux accélèrent l'itération ; ils ne changent pas les garanties de la CI.

- **FAST** — pendant une petite modification : syntaxe/compilation du fichier touché + test(s) directement concernés. Exemple Python : `python -m pytest -q <test::node>` ; frontend : `node --check <fichier.js>`. Un FAST vert signifie uniquement que ce périmètre rapide est vert.
- **TARGETED** — avant de considérer une couche localement terminée : tests de la couche + contrat(s) voisin(s). Exemples : Survey `python -m pytest -q tests/survey tests/pipeline/test_architectural_analysis_pipeline.py`; Scene `python -m pytest -q tests/scene tests/pipeline/test_architectural_scene_candidate.py`; export aval `python -m pytest -q tests/bricks/test_bom.py tests/bricks/test_assembly.py tests/bricks/test_instructions.py tests/bricks/test_bags.py tests/bricks/test_export.py`.
- **FULL** — obligatoire avant fusion d'un changement de code et pour tout changement transversal/architecture/géométrie/support : reproduire la CI, au minimum `python -m pytest -q`, puis les gardes frontend/pipeline/smoke réellement définies dans `.github/workflows/ci.yml`. La CI GitHub reste la preuve finale de ce workflow ; un sous-ensemble local ne la remplace pas.

Pour une modification purement documentaire, vérifier les liens/commandes cités et la cohérence avec le dépôt ; ne pas prétendre qu'une suite métier complète apporte une preuve supplémentaire sur le texte.

## 2. Démarrage approfondi si nécessaire

Si la reprise rapide ne suffit pas ou si le changement traverse plusieurs frontières :
1. lire `PROJECT_PRINCIPLES.md` ;
2. vérifier l'état réel de `main`, les commits récents, les PR/issues pertinentes et la CI/déploiement concernés ;
3. lire `README.md` ;
4. lire `PROGRESSION.md` pour identifier le chantier prioritaire, puis vérifier chacun de ses faits changeants contre le dépôt ;
5. consulter `docs/CURRENT_PROJECT_STATE.md` et `HANDOFF.md` seulement comme contexte/passation, jamais comme substitut à cette vérification ;
6. lire `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` et les contrats spécialisés concernés par la tâche ;
7. rechercher dans le code, les tests, les docs et les issues si le concept demandé existe déjà.

Ne jamais demander à l'utilisateur de reconstruire l'historique d'une conversation si le dépôt permet de le retrouver.

## 3. Deux classes d'information

### Constitution stable

Les règles qui doivent survivre aux conversations appartiennent à `PROJECT_PRINCIPLES.md`, aux ADR, aux contrats canoniques et aux tests. Elles bougent rarement et doivent être modifiées explicitement.

### État calculable

Les faits qui vieillissent rapidement doivent être mesurés au moment de la reprise :
- HEAD de `main` et commits récents ;
- PR/issues ouvertes ou récemment fusionnées ;
- dernière CI pertinente et son résultat ;
- fichiers, contrats, routes/endpoints et fonctions réellement présents ;
- tests réellement présents et, lorsque nécessaire, réellement exécutés ;
- chantier encore non résolu.

Ne pas considérer un SHA, numéro de PR, nombre de tests ou statut CI recopié dans une passation comme une vérité actuelle.

## 4. Carte des sources de vérité

- Constitution du projet : `PROJECT_PRINCIPLES.md`.
- Vision et pipeline : `README.md`.
- Progression opérationnelle et reprise immédiate : `PROGRESSION.md`.
- Contexte récent et archives d'état : `docs/CURRENT_PROJECT_STATE.md`, `HANDOFF.md` et documents de tranche datés/spécialisés.
- Architecture et raisons des décisions : `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`.
- Survey / Scene / raisonnement photo : `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md`, `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_REASONING_PASS.md`.
- Comportement garanti : contrats, code et tests correspondants.
- État technique courant : GitHub + état réel de `main`.

Ne pas recopier une règle durable dans plusieurs documents si un lien vers sa source canonique suffit.

## 5. Règles de travail

- Traiter le dépôt comme un logiciel existant, jamais comme un projet vierge.
- Préserver l'existant : ajouter/étendre avant de remplacer ou supprimer.
- Avant une suppression, vérifier si la demande exige réellement un retrait ou seulement un ajout/amélioration.
- Respecter les frontières métier déjà séparées ; ne pas fusionner des contrats pour simplifier localement le code.
- Ne jamais inventer géométrie, mesure, disponibilité, référence fournisseur ou certitude pour compléter artificiellement un résultat.
- Distinguer faits observés, hypothèses, estimations et inconnues.
- Corriger au niveau de la cause et ajouter une régression lorsqu'un défaut pourrait revenir.
- Vérifier le chemin réellement déployé lorsque la fonctionnalité dépend du frontend, d'un workflow ou d'un pipeline différent des tests unitaires.
- Ne solliciter l'utilisateur que pour une action ou décision réellement humaine ; continuer autonomement tant que le dépôt permet d'avancer.

## 6. Méthode d'exécution

Pour une demande : inspection → reconstruction de l'état réel → reformulation du besoin → recherche de l'existant → décision minimale compatible → implémentation → tests/régressions → CI/déploiement si pertinent → documentation/indexation → passation.

Pour les futurs petits lots, préférer : **objectif précis → risques → modification minimale → FAST → TARGETED → invariants sentinelles → régression si bug → FULL/CI selon risque → mise à jour minimale de la source de vérité → commit logique**. Ne pas mélanger fonctionnalité, refactoring, renommage ou nettoyage sans dépendance réelle.

Ne pas interrompre l'utilisateur pour une décision technique résoluble par le dépôt. Demander une intervention humaine seulement pour une vraie décision produit subjective, une donnée inaccessible, une autorisation ou une ambiguïté à conséquences importantes.

## 7. Indexation continue

Une information importante ne doit pas rester uniquement dans une conversation.

Classer chaque information dans sa bonne source :
- principe durable → `PROJECT_PRINCIPLES.md` seulement si réellement constitutionnel ;
- décision architecturale → `docs/DECISIONS.md` / documentation d'architecture ;
- contrat durable → document/contrat canonique + tests ;
- tâche ou dette restante → issue lorsque pertinent ;
- progression opérationnelle et point de reprise → `PROGRESSION.md` ;
- compte-rendu de tranche/historique → document spécialisé ou `docs/CURRENT_PROJECT_STATE.md` ;
- comportement garanti → test automatisé lorsque possible.

La passation doit pointer vers les sources canoniques au lieu de recopier leur contenu.

## 8. Protocole obligatoire avant passation

Avant de terminer une tranche substantielle :
1. vérifier `main`, PR/issues et CI/déploiement pertinents ;
2. inventorier fichiers, contrats et comportements ajoutés/modifiés ;
3. vérifier que toute décision durable est documentée dans sa source canonique ;
4. vérifier que les nouvelles régressions sont couvertes par des tests ;
5. rechercher les références devenues obsolètes ou contradictoires ;
6. garder `PROGRESSION.md` lisible et centré sur les progrès réels, les régressions, le chantier prioritaire, les blocages humains éventuels et les choses à ne pas refaire ;
7. éviter d'y recopier les faits calculables sauf comme repère explicitement daté ;
8. conserver les chronologies détaillées dans les ADR, PR/issues ou documents de tranche plutôt que dans le prompt de reprise ;
9. relire la reprise comme si le prochain agent n'avait accès à aucune conversation précédente ;
10. vérifier que le bloc « PROMPT OFFICIEL » en tête de ce fichier suffit effectivement à reprendre.

Une passation est réussie lorsque l'utilisateur n'a pas besoin de mémoriser le bon prompt ni de raconter ce qui s'est passé dans les conversations précédentes.
