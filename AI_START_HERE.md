# AI START HERE — Boldüngo / BrickHouse

Ce fichier est le point d’entrée obligatoire de tout agent IA qui reprend ce dépôt. Il n’est pas une nouvelle source de vérité métier : il indexe les sources existantes, impose une discipline de reprise et définit le protocole de passation.

## 1. Démarrage obligatoire

Avant toute modification :
1. vérifier l’état réel de `main`, les commits récents, issues/PR pertinentes et la CI/déploiement concernés ;
2. lire `README.md` ;
3. lire `NEXT_CONVERSATION.md`, puis les documents de passation qu’il référence ;
4. lire `docs/ARCHITECTURE.md` et les contrats spécialisés concernés par la tâche ;
5. rechercher dans le code, les tests, les docs et les issues si le concept demandé existe déjà.

`main` et les contrats/tests exécutables priment sur une passation devenue ancienne. Une passation décrit un point de reprise, pas une vérité supérieure au dépôt.

## 2. Carte des sources de vérité

- Vision et pipeline courant : `README.md`.
- Reprise immédiate / travail récent : `NEXT_CONVERSATION.md`.
- Architecture : `docs/ARCHITECTURE.md` et documents d’architecture spécialisés.
- Survey / Scene / raisonnement photo : `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md`, `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_REASONING_PASS.md`.
- Contrats de construction : documentation dédiée à `BrickModel`, BOM, `AssemblyPlan` et autres plans séparés, plus le code et les tests correspondants.
- État du travail : issues/PR GitHub et état réel de `main`.

Ne pas recopier une règle durable dans plusieurs documents si un lien vers sa source canonique suffit.

## 3. Règles de travail

- Traiter le dépôt comme un logiciel existant, jamais comme un projet vierge.
- Préserver l’existant : ajouter/étendre avant de remplacer ou supprimer.
- Avant une suppression, se demander si la demande exige réellement un retrait ou seulement un ajout/amélioration.
- Respecter les frontières métier déjà séparées ; ne pas fusionner des contrats pour simplifier localement le code.
- Ne jamais inventer géométrie, mesure, disponibilité, référence fournisseur ou certitude pour compléter artificiellement un résultat.
- Distinguer faits observés, hypothèses, estimations et inconnues.
- Corriger au niveau de la cause et ajouter une régression lorsqu’un défaut pourrait revenir.
- Vérifier le chemin réellement déployé lorsque la fonctionnalité dépend du frontend, d’un workflow ou d’un pipeline différent des tests unitaires.

## 4. Méthode d’exécution

Pour une demande : inspection → reformulation du besoin → recherche de l’existant → décision minimale compatible → implémentation → tests/régressions → CI/déploiement si pertinent → documentation/indexation → passation.

Ne pas interrompre l’utilisateur pour une décision technique résoluble par le dépôt. Demander une intervention humaine seulement pour une vraie décision produit subjective, une donnée inaccessible, une autorisation ou une ambiguïté à conséquences importantes.

## 5. Indexation continue

Une information importante ne doit pas rester uniquement dans une conversation.

Classer chaque information dans sa bonne source :
- contrat durable → document/contrat canonique + tests ;
- décision architecturale → documentation d’architecture ;
- tâche ou dette restante → issue ;
- état temporaire de reprise → passation ;
- comportement garanti → test automatisé lorsque possible.

La passation doit pointer vers les sources canoniques au lieu de les dupliquer intégralement.

## 6. Protocole obligatoire avant passation

Avant de terminer une tranche substantielle :
1. vérifier `git/main`, PR/issues et CI/déploiement pertinents ;
2. inventorier fichiers, contrats et comportements ajoutés/modifiés ;
3. vérifier que toute décision durable est documentée dans sa source canonique ;
4. vérifier que les nouvelles régressions sont couvertes par des tests ;
5. rechercher les références devenues obsolètes ou contradictoires dans README/docs/passation ;
6. mettre à jour la passation sans effacer l’historique encore utile ;
7. indexer clairement : FAIT ET VÉRIFIÉ / EN COURS / OUVERT / BLOQUÉ / PROCHAINE ÉTAPE / À NE PAS REFAIRE ;
8. inclure les identifiants utiles : issues, PR, commits, versions de contrat, commandes de validation ;
9. relire la passation comme si le prochain agent n’avait accès à aucune conversation précédente.

Une passation n’est complète que si un nouvel agent peut reprendre sans demander ce qui vient d’être fait ni réinventer l’architecture.

## 7. Instruction courte pour une nouvelle conversation

> Consulte `AI_START_HERE.md`, suis son ordre de lecture, vérifie l’état réel de `main` et des issues/PR/CI pertinentes, puis prends en charge ma demande sans repartir de zéro. Avant toute passation, applique intégralement le protocole d’indexation et de continuité du dépôt.
