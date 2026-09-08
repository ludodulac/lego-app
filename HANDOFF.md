# Boldüngo / BrickHouse — continuité

Dernière mise à jour : 2026-09-08

Ce fichier est la passation humaine précise à conserver entre conversations. Il complète `AI_START_HERE.md`, `PROGRESSION.md` et les contrats canoniques ; il ne les remplace pas.

Pour reprendre le projet :
1. lire `AI_START_HERE.md` ;
2. vérifier l’état réel de `main`, des PR/issues et de la CI/Pages ;
3. lire `PROGRESSION.md` et `PROJECT_PRINCIPLES.md` ;
4. utiliser ensuite uniquement les documents de la couche concernée ;
5. pour le test réel, reprendre directement `frontend/benchmarks/real-house-5/` et ne pas refaire Photos → Survey sauf changement intentionnel des preuves/du contrat.

## Objectif produit immédiat

L’objectif prioritaire est maintenant d’obtenir rapidement un premier prototype Boldüngo réellement visible et reconnaissable de la maison test, puis de l’utiliser comme support de correction humaine. Éviter documentation supplémentaire, grands refactors ou architecture spéculative tant qu’ils ne débloquent pas directement ce parcours.

Pipeline cible : photos → ArchitecturalSurvey → ArchitecturalScene → validation spatiale/topologique → planification de représentation LEGO → BrickModel → validation physique → BOM / AssemblyPlan / InstructionPlan / BagPlan → viewer/export.

Ordre de vérité :
- `ArchitecturalSurvey v0.1` = autorité sémantique/observationnelle ;
- `ArchitecturalScene v0.2` = autorité métrique/géométrique/spatiale ;
- les contraintes LEGO ne réécrivent jamais silencieusement Survey/Scene ;
- une simplification LEGO reste explicite et traçable ;
- unknown stays unknown ;
- proximité visuelle ≠ support physique.

## Cas réel `real-house-5`

Les cinq photos originales sont déjà dans `frontend/benchmarks/real-house-5/`. Le Survey accepté existe également et son checkpoint indique `known_measurements_count = 0`. Ne jamais réintroduire l’ancienne mesure benchmark de 10 m dans ce cas réel.

Orientation humaine confirmée le 8 septembre 2026 :
1. photo 1 = façade avant ;
2. photo 2 = côté droit, le long de la rue qui monte ;
3. photo 3 = côté gauche, vue plus large, allant davantage vers la terrasse/arrière ;
4. photo 4 = côté gauche, vue plus rapprochée autour de l’escalier/volume extérieur/terrasse ;
5. photo 5 = arrière partiellement observable.

La façade arrière réelle du bâtiment cible est normalement plane (information fournie par l’utilisateur), mais la vue arrière est fortement dégradée/incomplète : une ancienne construction a été démolie et seule une partie du mur cible est réellement observable. Ne jamais inventer des ouvertures, détails ou volumes arrière cachés. Le caractère plan peut être conservé comme information humaine traçable, sans promouvoir le contenu invisible en vérité observée.

## Une maison cible, plusieurs vues

Le logiciel doit comprendre par défaut que la série de photos fait le tour d’un seul bâtiment cible, sauf demande explicite contraire de l’utilisateur. Il ne doit pas raisonner « une photo = une façade indépendante » ni absorber automatiquement tout ce qui apparaît dans l’image.

Il faut suivre l’identité du même bâtiment à travers les vues et distinguer :
- ce qui appartient au bâtiment cible ;
- le contexte utile mais non cible (poteaux, végétation, véhicules, bâtiments voisins, restes d’ancienne construction, etc.) ;
- les occlusions ;
- les zones détruites/non observables ;
- les zones réellement inconnues.

Exemple côté droit : le poteau électrique constitue une forte occlusion/limite visuelle. Quand la preuve du bâtiment disparaît derrière lui, ne pas prolonger artificiellement la maison ni incorporer ce qui est derrière. Une autre vue peut résoudre une zone seulement si elle apporte une preuve réelle.

Si l’utilisateur demande explicitement plusieurs bâtiments, une annexe séparée, un mur, etc., la cible peut être élargie. Par défaut : un bâtiment principal.

## Problème spatial caractéristique à résoudre avant le LEGO

Le défaut historique le plus important du prototype réel est la mauvaise compréhension des éléments complexes du côté gauche. Avant de remplir avec des briques, la Scene doit représenter correctement les espaces/volumes occupés et leurs relations.

Points à vérifier particulièrement sur `real-house-5` :
- terrasse bois : emprise spatiale, niveau relatif quand prouvé, raccord au bâtiment et supports visibles ;
- escalier extérieur : géométrie/cheminement en L, pas une simple volée droite si les preuves montrent le L ;
- palier/volume maçonné : espace distinct de la terrasse bois et relation avec l’escalier ;
- supports de terrasse : notamment la géométrie visible de poteau/contreventement en Y ;
- raccords entre terrasse, palier, escalier, façade et volumes/toitures ;
- épaisseurs/retraits/profondeurs de mur lorsqu’ils constituent une particularité visible de la maison ;
- fenêtres/portes : identité, position, composition/type quand prouvé.

La règle est : d’abord établir la vérité architecturale et les espaces ; ensuite seulement choisir comment ces espaces sont représentés en LEGO.

## Vérité architecturale vs représentation LEGO

Au stade Survey/Scene, ne pas « tricher » pour arranger le catalogue LEGO. Préserver les détails précis qui sont réellement prouvés, y compris positions, relations, niveaux relatifs, épaisseurs/retraits et caractéristiques architecturales.

Après validation de la Scene, la représentation LEGO peut être simplifiée de façon bornée, explicite et traçable pour obtenir un modèle reconnaissable, constructible, esthétique et agréable à construire.

Exemple terrasse : l’existence d’un plancher bois, son emprise et ses relations architecturales peuvent être importantes ; le nombre exact de planches visibles n’a pas nécessairement à être reproduit. La planification LEGO peut choisir un nombre raisonnable d’éléments qui symbolise correctement le plancher, tant que la terrasse reste dans le bon volume et respecte les relations importantes.

Les images LEGO de référence fournies le 8 septembre servent uniquement à illustrer le niveau de résultat souhaité : une maquette architecturale mignonne/soignée, reconnaissable, réelle dans ses caractéristiques principales et constructible. Elles ne sont pas des preuves architecturales de la maison et ne doivent jamais être copiées comme géométrie.

## Hypothèses nécessaires au premier prototype

Ne pas confondre une hypothèse de représentation avec une vérité architecturale. Si un détail invisible n’est pas indispensable, le laisser inconnu/absent. Si un choix est indispensable pour produire un prototype LEGO, une simplification provisoire peut être choisie dans la couche de représentation, explicitement marquée comme telle et révisable, sans modifier Survey/Scene.

Exemple important : l’utilisateur précise que le plancher bois de la terrasse est en réalité plus bas que l’arrivée de l’escalier/palier béton. Si cette différence de niveau n’est pas prouvable depuis les photos, ne pas la déclarer observation visuelle. Elle peut être ajoutée comme information humaine si l’utilisateur la confirme comme fait architectural ; sinon une représentation provisoire simple peut être utilisée uniquement dans la couche LEGO.

Le premier prototype n’a pas besoin d’être définitif. Il doit être honnête, suffisamment complet et surtout reconnaissable afin que l’utilisateur puisse corriger visuellement les erreurs. Ne pas attendre la perfection de chaque planche/fenêtre/détail avant d’afficher un résultat.

## Questions humaines ciblées

L’IA peut et doit demander à l’utilisateur une information quand un trou réel bloque une décision importante. Ne pas demander des mesures ou classifications par réflexe.

Exemple : si une ouverture est certaine mais son type est ambigu et que le choix est nécessaire à la représentation, demander de façon ciblée : porte pleine, porte vitrée/porte-fenêtre, autre ?

BH-182 doit produire la demande humaine minimale dérivée d’un vrai blocker/readiness diagnostic. Ne jamais inventer une valeur numérique, une pente, une coordonnée, un support ou un objet pour éviter de poser une question nécessaire.

## Ouvertures et catalogue LEGO

Le principe attendu est :
1. Scene architecturale précise et indépendante du catalogue ;
2. choisir ensuite des familles LEGO compatibles pour les ancres architecturales (fenêtres, portes, toit, terrasse, escalier, cheminée, etc.) ;
3. réserver leurs empreintes ;
4. adapter seulement ensuite, de façon minimale et traçable, le remplissage/résidu des murs autour de ces ancres.

Si une porte-fenêtre LEGO disponible et une porte/fenêtre ont des empreintes différentes, ce n’est pas Survey/Scene qui doit être falsifié. Le RepresentationPlan choisit une solution catalogue et documente l’ajustement LEGO borné.

Une ouverture connue ne doit pas disparaître en trou générique si son type est important. Une ouverture réellement inconnue reste inconnue jusqu’à preuve ou réponse humaine.

## Constructibilité

Aucune pièce LEGO ne doit flotter dans le vide. Toute pièce/sous-assemblage généré doit disposer d’une chaîne de support/connectivité modélisée vers une base/structure via une connexion LEGO reconnue. La proximité géométrique seule n’est pas une preuve de support.

Pour la maison réelle, cela concerne particulièrement terrasse, poteaux/contreventements, escalier, toiture, cheminée et détails rapportés.

## Seuil de réussite immédiat

Le prochain objectif n’est pas « modèle final parfait ». C’est un premier viewer dans lequel l’utilisateur reconnaît sa maison et peut commencer une correction utile.

Ce premier résultat devrait déjà préserver autant que les preuves le permettent :
- volume principal et toiture ;
- rythme/position générale des ouvertures ;
- terrain/pente pertinente quand représentable ;
- côté gauche caractéristique avec terrasse + palier/volume + escalier ;
- cheminée ;
- volumes secondaires réellement prouvés.

Les éléments prouvés sont fidèles ; les inconnus indispensables à un prototype ne peuvent recevoir qu’une simplification LEGO provisoire explicite ; les inconnus non indispensables restent absents/inconnus.

## Marche à suivre immédiate

Ne pas recommencer Photos → Survey pour le benchmark accepté. Partir du Survey accepté et confronter le pipeline réel :

`accepted Survey → Scene candidate → spatial/topological validation → strict readiness → minimal human requests si réellement nécessaires → LEGO RepresentationPlan → BrickModel → physical validation → viewer/export`.

Auditer en priorité si la Scene actuelle sait réellement exprimer l’escalier en L, l’emprise/niveau de terrasse, le palier/volume maçonné, le support/contreventement en Y, les relations spatiales et les ouvertures. Le premier défaut générique empêchant cette vérité spatiale devient le prochain petit lot : cause générique → correction minimale → test de régression → CI → reprise immédiate du benchmark réel.

L’objectif est d’arriver vite à quelque chose de visible, sans sacrifier les frontières de vérité.

## État récent à ne pas régresser

- PR #569 (workflow de reprise rapide dans `AI_START_HERE.md`) : fusionnée.
- PR #568 / BH-184 (capability summary d’export conservateur) : fusionnée ; merge `f517fd4ac966f2b23cedd4945619c5abb7983e53` ; les quatre workflows post-merge observés étaient verts.
- `mechanical_verification` reste `not_claimed` par défaut ; une affirmation positive nécessite un validator nommé et des scopes explicites.
- `contract_verified` signifie cohérence contractuelle interne, pas validation mécanique générale, déploiement, procurement ou validation réelle utilisateur.
- le benchmark `real-house-5` possède un Survey accepté et zéro mesure connue.

## Confidentialité / sources

Ne plus chercher quoi que ce soit dans Google Drive pour Boldüngo. Utiliser GitHub `ludodulac/lego-app` et les fichiers/photos fournis directement dans la conversation.

Les photos réelles sont des données de travail. Ne pas les publier/committer automatiquement ailleurs sans raison. Elles existent déjà dans le benchmark du dépôt ; préférer des fixtures dérivées/anonymisées pour les nouveaux tests génériques quand elles suffisent.

## Sources canoniques

- reprise rapide : `AI_START_HERE.md` ;
- progression opérationnelle : `PROGRESSION.md` ;
- principes : `PROJECT_PRINCIPLES.md` ;
- vision/pipeline : `README.md` ;
- état vérifié : `docs/CURRENT_PROJECT_STATE.md` ;
- architecture/décisions : `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` ;
- Survey/Scene : `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md`, `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_REASONING_PASS.md` ;
- historique ancien : `docs/HANDOFF_HISTORY_2026-08-23.md`.

Instruction minimale pour une nouvelle conversation :

> Lis `AI_START_HERE.md`, `PROGRESSION.md`, `PROJECT_PRINCIPLES.md` et `HANDOFF.md`, vérifie `main`/CI, puis reprends le benchmark `real-house-5` au stade Survey → Scene. Priorité : obtenir rapidement un premier modèle reconnaissable dans le viewer sans inventer la vérité architecturale.
