# Boldüngo / BrickHouse — état courant vérifié

Date de passation : 2026-08-31

Ce document est l’index opérationnel du travail récent. Il complète `AI_START_HERE.md` et pointe vers les contrats/tests réels. `main` reste la source technique de vérité.

## FAIT ET VÉRIFIÉ

### État Git / déploiement

Au début de cette passation, `main` pointe sur `62655f6e1bd33c3ea469fe10af2ada27c586a889`, merge de la PR #305. La CI de `main` (run 1257) et le déploiement GitHub Pages (run 514) sont tous deux terminés avec succès. Toujours revérifier ces valeurs avant de reprendre : cette section décrit un point de contrôle, pas un verrou éternel.

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

Le flux one-shot `external-bundle-0.1` est seulement une compatibilité historique ; ne pas le rétablir comme workflow principal.

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
- #305 : audit de complétude topologique Photos → Survey, additif après l’audit terrain.

Les SHA exacts utiles sont conservés dans l’historique Git ; ne pas recopier leur logique dans de nouvelles règles sans lire le code/tests concernés.

### Moteur géométrique LEGO

Le sous-package `lego_geometry_engine/` est désormais intégré. L’adaptateur principal est `backend/brickhouse/bricks/geometry_adapter.py`.

Capacités actuelles :
- triangles LDraw transformés ;
- broad phase AABB ;
- collision/contact en narrow phase ;
- ray-casting de containment ;
- topologie de support ;
- connecteurs exacts utilisés pour distinguer contact légal et collision.

Limites connues : pas encore de modèle général complet pour Technic, clips, charnières, SNOT, contraintes mécaniques, stress ou stabilité globale.

## BENCHMARK RÉEL ACTUEL

Le benchmark humain principal reste la même maison, avec 5 photos originales et une largeur réelle de façade avant de 10 m. Échelle de test habituelle : 48 studs.

Le dernier Survey neutre observé après #304 a confirmé que l’audit terrain fonctionne :
- terrain droit visible comme pente certaine montant de l’avant vers l’arrière ;
- quatre façades auditées pour le terrain ;
- aucune amplitude numérique inventée.

Ce même Survey a exposé un défaut distinct : absence de `building_boundary` et absence de relations `connects_to` vers le bâtiment malgré une plateforme décrite comme attachée. La PR #305 corrige ce défaut au niveau du handoff avec un audit topologique additif.

Ne pas réutiliser un JSON de conversation comme fixture canonique si le fichier n’est pas présent dans le dépôt. Le prochain run humain doit produire un nouveau Survey depuis le build déployé après #305.

## CONTRATS PROMPT ACTUELS À PRÉSERVER

Photos → Survey :
- prompt historique `frontend/brickhouse-survey-prompt.txt` conservé ;
- audit terrain additif : `frontend/brickhouse-survey-terrain-audit-v29.txt` ;
- wrapper terrain : `frontend/brickhouse-survey-package-v05.js` ;
- audit topologique additif : `frontend/brickhouse-survey-topology-audit-v30.txt` ;
- wrapper topologique : `frontend/brickhouse-survey-package-v06.js` ;
- point d’entrée stable : `frontend/brickhouse-survey-package.js`.

Invariant important : ne pas condenser/réécrire le prompt historique pour ajouter une règle. Les audits récents sont volontairement des couches additives, car une tentative de remplacement direct avait supprimé des garde-fous historiques et fait échouer les régressions.

Survey → Scene :
- workflow principal exposé depuis #302 ;
- handoff v4.3 ;
- le Survey reste l’autorité sémantique ;
- le PDF original sert d’évidence géométrique supplémentaire ;
- `terrain.profiles` est le contrat canonique Scene ;
- une cheminée certaine du Survey ne doit pas être omise si sa géométrie peut être bornée honnêtement.

## OUVERT

### BH-090 / #274 — validation humaine bout-en-bout

Toujours ouvert. L’étape automatisée a été faite, puis plusieurs défauts génériques ont été découverts et corrigés. Le prochain passage humain doit reprendre uniquement une fois les audits actuels déployés.

### Régressions encore à contrôler avant de considérer Photos → Survey robuste

Le dernier Survey neutre avant #305 a montré trois autres points à vérifier lors du prochain run, sans inventer de correction benchmark-spécifique :

1. `capture_role:"targeted_detail"` a été émis avec `facade:"left"`, alors que le contrat historique demande normalement `facade:null` pour une vue ciblée. Vérifier le schéma backend et le nouveau résultat avant toute correction.
2. L’observation toiture était certaine mais sans hypothèse qualitative utile, malgré plusieurs vues. Vérifier si le prompt actuel exige réellement un attribut qualitatif soutenu et, si nécessaire, corriger par audit générique additif — jamais en imposant `gable` à cette maison.
3. La chaîne qualitative de pente terrain a été émise sous la forme `rises_front_to_rear`; vérifier que Survey → Scene accepte cette sémantique sans dépendre d’un vocabulaire exact comme `front_to_rear_up`.

### Contradiction documentaire connue à vérifier

`frontend/brickhouse-survey-to-scene-prompt.txt` a historiquement contenu une mention ancienne `terrain.facade_grade_profiles` alors que le contrat Scene actuel est `terrain.profiles`. Le wrapper #303 impose le contrat canonique, mais le prompt de base doit être relu et corrigé minimalement si la ligne obsolète existe encore.

### Fidélité visuelle / modèle encore non résolue

Une fois le round-trip sémantique robuste :
- fenêtres encore schématiques ;
- cadres, retraits, appuis et linteaux partiels ;
- terrasse approximative ;
- escalier approximatif ;
- position de cheminée encore estimée selon l’évidence ;
- terrain/rue et trottoir incomplets dans le rendu final.

Ne pas inventer des dimensions architecturales pour améliorer l’apparence. Une absence de primitive Scene ou d’évidence doit rester une limitation explicite.

## EN COURS

La présente passation documentaire est préparée sur une branche dédiée. Elle doit être fusionnée uniquement après CI verte et contrôle de cohérence.

## BLOQUÉ

Aucun blocage technique connu au moment de cette passation. Le prochain vrai point nécessitant l’utilisateur est un nouveau run humain Photos → Survey, mais seulement après fusion/déploiement de la passation et vérification finale des contrats documentaires.

## PROCHAINE ÉTAPE

Pour la prochaine conversation :
1. lire `AI_START_HERE.md` ;
2. vérifier le SHA réel de `main`, CI, Pages, PR/issues ouvertes ;
3. vérifier/corriger les contradictions prompt/contrat listées ci-dessus sans demander encore un nouveau run humain ;
4. seulement quand le dépôt est cohérent et déployé, demander un unique nouveau run utilisateur avec les mêmes 5 photos et largeur avant 10 m ;
5. auditer le Survey retourné intact avant de lancer Survey → Scene.

## À NE PAS REFAIRE

- ne pas demander à l’utilisateur de régénérer un benchmark à chaque petit correctif ;
- ne pas modifier le JSON utilisateur pour le faire passer ;
- ne pas assouplir un schéma pour accepter une pseudo-Survey/pseudo-Scene ;
- ne pas laisser les contraintes LEGO modifier la Scene ;
- ne pas réécrire les prompts historiques en supprimant des garde-fous ;
- ne pas coder de règle spécifique à la maison test ;
- ne pas faire passer artificiellement un test : un échec reproductible est une information à comprendre et corriger.

## Validation de reprise

Une nouvelle conversation doit pouvoir commencer par :

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet.

Si cette instruction ne suffit plus, ce document et `NEXT_CONVERSATION.md` doivent être mis à jour avant la prochaine passation.
