# Boldüngo / BrickHouse — état courant vérifié

Date de passation : 2026-08-31

Ce document est l’index opérationnel du travail récent. Il complète `AI_START_HERE.md` et pointe vers les contrats/tests réels. `main` reste la source technique de vérité.

## FAIT ET VÉRIFIÉ

### État Git / déploiement

La passation complète a été fusionnée via la PR #306. Son merge a produit `main` = `efb9095f3d249d5f27efea246d68c004145aa2ef`. La CI de `main` correspondante (run 1259) est terminée avec succès et le déploiement GitHub Pages correspondant (run 515) est terminé avec succès. La PR historique #296, devenue obsolète, a été fermée comme supersédée par #306.

Toujours revérifier l’état réel de `main` au début d’une nouvelle conversation : les SHA et runs ci-dessus sont le point de contrôle de cette passation, pas une valeur éternelle.

### Pipeline architectural de référence

Le principe durable est :

`PHOTOS → vérité architecturale → scène architecturale métrique → construction LEGO → validation physique LEGO → modèle`

Les responsabilités sont séparées :
- le Survey est l’autorité sémantique/observée ;
- la Scene est l’autorité métrique/géométrique ;
- les contraintes LEGO ne doivent jamais réécrire silencieusement la vérité architecturale ;
- les pertes de fidélité LEGO doivent être explicites.

Voir `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md`, `docs/ARCHITECTURAL_SURVEY_V01.md`, `docs/ARCHITECTURAL_SCENE_V02.md` et `docs/DECISIONS.md`.

### Round-trip manuel Boldüngo → ChatGPT

L’issue #274 / BH-090 reste le jalon de validation bout-en-bout. Le workflow principal actif est en deux étapes :
1. Photos → `ArchitecturalSurvey v0.1` ;
2. Survey validé + PDF photo original → `ArchitecturalScene v0.2`.

Le flux one-shot `external-bundle-0.1` est seulement une compatibilité historique ; ne pas le rétablir comme workflow principal. L’issue #274 contient désormais un commentaire de continuité daté de cette passation avec le dernier état du benchmark.

### Corrections structurantes récentes

Les PR suivantes sont fusionnées et font partie de l’état actuel :
- #283 : compatibilité métrique Platform/Stair `PropertyValue` vs scalaire ;
- #285 : validation de contact métrique pour relations `semantic_anchor` résolues ;
- #288 : raisonnement architectural v4.2, identité/topologie d’abord, hypothèses concurrentes, solve métrique conjoint et passe de contradictions ;
- #290 : compatibilité des métadonnées racine Scene `id`/`name` manquantes ;
- #292 : compatibilité cheminée générique → `SceneChimney` dans le cas précisément justifié par le Survey ;
- #294 : longueur longitudinale de toiture rendue tileable sans modifier la maison ; fallback DP exact pour le tuilage ;
- #295 : moteur LEGO Geometry & Assembly, intégré au dépôt ;
- #297 : les pentes physiques de toiture ne pénètrent plus le remplissage de pignon ;
- #298 : régression maison réelle pour toiture peu pentue 18° ;
- #299 : ouverture physique de toiture autour des cheminées métriques ;
- #300 : régression LDraw cheminée + correction de l’accouplement de connecteurs tournés ;
- #301 : préservation d’une pente de terrain qualitative sans inventer d’amplitude ;
- #302 : exposition du handoff Survey → Scene v4.3 dans le workflow principal ;
- #303 : sérialisation canonique de `terrain.profiles` et des cheminées dans le handoff Scene ;
- #304 : audit terrain Photos → Survey, additif au prompt historique ;
- #305 : audit de complétude topologique Photos → Survey, additif après l’audit terrain ;
- #306 : passation dépôt complète, sources de vérité remises à jour et contradiction terrain du prompt Scene supprimée.

### Moteur géométrique LEGO

Le sous-package `lego_geometry_engine/` est désormais intégré. L’adaptateur principal est `backend/brickhouse/bricks/geometry_adapter.py`.

Capacités actuelles : triangles LDraw transformés, broad phase AABB, collision/contact narrow phase, ray-casting de containment, topologie de support et connecteurs exacts pour distinguer contact légal/collision.

Limites connues : pas encore de modèle général complet pour Technic, clips, charnières, SNOT, contraintes mécaniques, stress ou stabilité globale.

### Contrat terrain Scene rendu cohérent

La contradiction documentaire du prompt Survey → Scene a été supprimée : le contrat de collection est `terrain.profiles`, tandis que `terrain.kind` peut rester `"facade_grade_profiles"`. `tests/test_scene_prompt_terrain_contract.py` verrouille cette distinction.

## BENCHMARK RÉEL ACTUEL

Le benchmark humain principal reste la même maison, avec 5 photos originales et une largeur réelle de façade avant de 10 m. Échelle de test habituelle : 48 studs.

Le dernier Survey neutre observé après #304 a confirmé que l’audit terrain fonctionne : terrain droit certain montant de l’avant vers l’arrière, quatre façades auditées, aucune amplitude numérique inventée.

Ce même Survey a exposé un défaut distinct : absence de `building_boundary` et absence de relations `connects_to` vers le bâtiment malgré une plateforme décrite comme attachée. #305 corrige ce défaut via un audit topologique additif.

Ne pas réutiliser un JSON de conversation comme fixture canonique si le fichier n’est pas présent dans le dépôt. Le prochain run humain doit produire un nouveau Survey depuis le build déployé après ces corrections.

## CONTRATS PROMPT ACTUELS À PRÉSERVER

Photos → Survey :
- prompt historique `frontend/brickhouse-survey-prompt.txt` conservé ;
- audit terrain additif : `frontend/brickhouse-survey-terrain-audit-v29.txt` ;
- wrapper terrain : `frontend/brickhouse-survey-package-v05.js` ;
- audit topologique additif : `frontend/brickhouse-survey-topology-audit-v30.txt` ;
- wrapper topologique : `frontend/brickhouse-survey-package-v06.js` ;
- point d’entrée stable : `frontend/brickhouse-survey-package.js`.

Invariant : ne pas condenser/réécrire le prompt historique pour ajouter une règle. Les audits récents sont volontairement des couches additives, car une tentative de remplacement direct avait supprimé des garde-fous historiques et fait échouer les régressions.

Survey → Scene : handoff v4.3 ; Survey autorité sémantique ; PDF original preuve géométrique supplémentaire ; `terrain.profiles` collection canonique ; `terrain.kind:"facade_grade_profiles"` discriminant valide ; une cheminée certaine ne doit pas être omise si sa géométrie peut être bornée honnêtement.

## OUVERT

### BH-090 / #274 — validation humaine bout-en-bout

Toujours ouvert. L’étape automatisée et plusieurs corrections génériques sont terminées. Le prochain passage humain ne doit avoir lieu qu’après les contrôles automatiques restants ci-dessous.

### Trois drifts à contrôler avant le prochain run humain

1. `capture_role:"targeted_detail"` a été émis avec `facade:"left"`, alors que le contrat historique demande normalement `facade:null` pour une vue ciblée. Vérifier le schéma backend et le chemin de génération avant toute correction.
2. L’observation toiture était certaine mais sans hypothèse qualitative utile malgré plusieurs vues. Vérifier le contrat actuel et, si nécessaire, corriger par audit générique additif — jamais en imposant `gable` à la maison benchmark.
3. La pente terrain a été émise sous la forme `rises_front_to_rear`; vérifier que Survey → Scene accepte la sémantique sans dépendre d’un token exact comme `front_to_rear_up`.

### Fidélité visuelle / physique restante

Après stabilisation du round-trip : fenêtres encore schématiques ; cadres/retraits/appuis/linteaux partiels ; terrasse et escalier approximatifs ; position de cheminée prudente/estimée ; terrain/rue/trottoir incomplets dans le rendu final. Ne jamais inventer des dimensions architecturales pour améliorer l’apparence.

## EN COURS

Aucune tranche fonctionnelle n’est laissée en cours par cette passation. La petite clôture documentaire qui actualise ce point de contrôle n’introduit aucun changement fonctionnel ; son propre état doit toujours être vérifié sur `main` par le prochain agent.

## BLOQUÉ

Aucun blocage technique connu.

## PROCHAINE ÉTAPE

1. Lire `AI_START_HERE.md` et revérifier `main`, CI, Pages, PR/issues.
2. Examiner les trois drifts ci-dessus dans le code/schéma/prompt avant de demander un nouveau run humain.
3. Corriger uniquement les défauts génériques démontrés, avec régressions.
4. Une fois ces contrôles fusionnés/déployés, demander un unique nouveau run Photos → Survey avec les mêmes 5 photos et la largeur avant 10 m.
5. Auditer le Survey retourné intact avant Survey → Scene.

## À NE PAS REFAIRE

- ne pas demander à l’utilisateur de régénérer un benchmark à chaque petit correctif ;
- ne pas modifier le JSON utilisateur pour le faire passer ;
- ne pas assouplir un schéma pour accepter une pseudo-Survey/pseudo-Scene ;
- ne pas laisser les contraintes LEGO modifier la Scene ;
- ne pas réécrire les prompts historiques en supprimant des garde-fous ;
- ne pas coder de règle spécifique à la maison test ;
- ne pas faire passer artificiellement un test reproductible qui échoue.

## Validation de reprise

Une nouvelle conversation doit pouvoir commencer par :

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet.

Si cette instruction ne suffit plus, `AI_START_HERE.md`, ce document et `NEXT_CONVERSATION.md` doivent être mis à jour avant la prochaine passation.
