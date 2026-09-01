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

## 1. Démarrage obligatoire

Avant toute modification :
1. lire `PROJECT_PRINCIPLES.md` ;
2. vérifier l’état réel de `main`, les commits récents, les PR/issues pertinentes et la CI/déploiement concernés ;
3. lire `README.md` ;
4. lire `NEXT_CONVERSATION.md` pour identifier le chantier prioritaire, puis vérifier chacun de ses faits changeants contre le dépôt ;
5. consulter `docs/CURRENT_PROJECT_STATE.md` et `HANDOFF.md` seulement comme contexte/passation, jamais comme substitut à cette vérification ;
6. lire `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` et les contrats spécialisés concernés par la tâche ;
7. rechercher dans le code, les tests, les docs et les issues si le concept demandé existe déjà.

Ne jamais demander à l’utilisateur de reconstruire l’historique d’une conversation si le dépôt permet de le retrouver.

## 2. Deux classes d’information

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

## 3. Carte des sources de vérité

- Constitution du projet : `PROJECT_PRINCIPLES.md`.
- Vision et pipeline : `README.md`.
- Reprise immédiate : `NEXT_CONVERSATION.md`.
- Contexte récent et archives d’état : `docs/CURRENT_PROJECT_STATE.md`, `HANDOFF.md` et documents de tranche datés/spécialisés.
- Architecture et raisons des décisions : `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`.
- Survey / Scene / raisonnement photo : `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md`, `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_REASONING_PASS.md`.
- Comportement garanti : contrats, code et tests correspondants.
- État technique courant : GitHub + état réel de `main`.

Ne pas recopier une règle durable dans plusieurs documents si un lien vers sa source canonique suffit.

## 4. Règles de travail

- Traiter le dépôt comme un logiciel existant, jamais comme un projet vierge.
- Préserver l’existant : ajouter/étendre avant de remplacer ou supprimer.
- Avant une suppression, vérifier si la demande exige réellement un retrait ou seulement un ajout/amélioration.
- Respecter les frontières métier déjà séparées ; ne pas fusionner des contrats pour simplifier localement le code.
- Ne jamais inventer géométrie, mesure, disponibilité, référence fournisseur ou certitude pour compléter artificiellement un résultat.
- Distinguer faits observés, hypothèses, estimations et inconnues.
- Corriger au niveau de la cause et ajouter une régression lorsqu’un défaut pourrait revenir.
- Vérifier le chemin réellement déployé lorsque la fonctionnalité dépend du frontend, d’un workflow ou d’un pipeline différent des tests unitaires.
- Ne solliciter l’utilisateur que pour une action ou décision réellement humaine ; continuer autonomement tant que le dépôt permet d’avancer.

## 5. Méthode d’exécution

Pour une demande : inspection → reconstruction de l’état réel → reformulation du besoin → recherche de l’existant → décision minimale compatible → implémentation → tests/régressions → CI/déploiement si pertinent → documentation/indexation → passation.

Ne pas interrompre l’utilisateur pour une décision technique résoluble par le dépôt. Demander une intervention humaine seulement pour une vraie décision produit subjective, une donnée inaccessible, une autorisation ou une ambiguïté à conséquences importantes.

## 6. Indexation continue

Une information importante ne doit pas rester uniquement dans une conversation.

Classer chaque information dans sa bonne source :
- principe durable → `PROJECT_PRINCIPLES.md` seulement si réellement constitutionnel ;
- décision architecturale → `docs/DECISIONS.md` / documentation d’architecture ;
- contrat durable → document/contrat canonique + tests ;
- tâche ou dette restante → issue lorsque pertinent ;
- point de reprise temporaire → `NEXT_CONVERSATION.md` ;
- compte-rendu de tranche/historique → document spécialisé ou `docs/CURRENT_PROJECT_STATE.md` ;
- comportement garanti → test automatisé lorsque possible.

La passation doit pointer vers les sources canoniques au lieu de recopier leur contenu.

## 7. Protocole obligatoire avant passation

Avant de terminer une tranche substantielle :
1. vérifier `main`, PR/issues et CI/déploiement pertinents ;
2. inventorier fichiers, contrats et comportements ajoutés/modifiés ;
3. vérifier que toute décision durable est documentée dans sa source canonique ;
4. vérifier que les nouvelles régressions sont couvertes par des tests ;
5. rechercher les références devenues obsolètes ou contradictoires ;
6. garder `NEXT_CONVERSATION.md` court : chantier prioritaire, blocage humain éventuel, fichiers/sources à lire et choses à ne pas refaire ;
7. éviter d’y recopier les faits calculables sauf comme repère explicitement daté ;
8. conserver les chronologies détaillées dans les ADR, PR/issues ou documents de tranche plutôt que dans le prompt de reprise ;
9. relire la reprise comme si le prochain agent n’avait accès à aucune conversation précédente ;
10. vérifier que le bloc « PROMPT OFFICIEL » en tête de ce fichier suffit effectivement à reprendre.

Une passation est réussie lorsque l’utilisateur n’a pas besoin de mémoriser le bon prompt ni de raconter ce qui s’est passé dans les conversations précédentes.
