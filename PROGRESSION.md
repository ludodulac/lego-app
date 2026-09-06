# Boldüngo / BrickHouse — progression

Dernière mise à jour : 2026-09-06

Ce fichier est la source unique de progression opérationnelle à consulter pour savoir où en est réellement le projet et quelles sont les prochaines briques de travail. Il ne remplace pas `PROJECT_PRINCIPLES.md`, les ADR, les contrats ou les tests. L'état réel de `main`, des PR/issues, de la CI et de Pages reste à revérifier avant toute action.

## Philosophie à préserver

La mission reste : transformer des preuves architecturales, notamment des photos, en une représentation structurée et traçable permettant de produire une maquette LEGO fidèle et des instructions de construction, sans inventer ce que les preuves ne permettent pas d'établir.

Le contrôle visuel humain du cas réel a clarifié une condition préalable : **avant de chercher à embellir ou remplir en LEGO, le logiciel doit savoir précisément où sont les objets architecturaux, quelle place ils occupent et comment ils s'imbriquent.** Une terrasse, un escalier, une cheminée, une toiture ou une ouverture correctement nommés mais mal situés constituent une reconstruction fausse.

Ordre de priorité du résultat :

1. vérité spatiale/topologique de la Scene : objets, extents, côté, ordre, niveaux, contacts, supports, débords/retraits et relations ;
2. reconnaissance de la silhouette et des volumes ;
3. proportions architecturales ;
4. composition des ouvertures ;
5. relations et éléments caractéristiques de la maison ;
6. matériaux/couleurs lorsqu'ils sont établis ;
7. détails architecturaux ;
8. exactitude locale du choix/placement des briques.

La géométrie LEGO ne doit jamais devenir plus importante que la fidélité architecturale. Une amélioration de placement de briques qui rend la maison moins reconnaissable est une régression produit.

## Cadre de décision — les quatre vérités

Le moteur doit maintenir quatre niveaux distincts et traçables :

1. **Vérité architecturale — qu'est réellement la maison ?** Les photos et autres preuves établissent volumes, orientations, niveaux, toiture, ouvertures, terrasse, escalier, cheminées, terrain et relations. L'incertitude reste explicite et cette vérité ne se déforme pas pour faciliter le LEGO.
2. **Vérité du catalogue LEGO — quelles pièces le moteur sait-il réellement utiliser ?** Dimensions, orientations, familles, rôles architecturaux et capacités de connexion doivent venir d'un vocabulaire validé. Une pièce ou subdivision non connue ne doit pas être inventée.
3. **Vérité constructive — est-ce réellement assemblable ?** Contacts, tenons/tubes, supports, collisions, gravité, continuité des murs, appui de toiture, stabilité et ordre d'assemblage sont des contraintes de faisabilité, pas des objectifs esthétiques facultatifs.
4. **Vérité de représentation — quel compromis LEGO conserve le mieux l'architecture ?** Lorsque le catalogue ne correspond pas exactement au réel, le moteur choisit le meilleur compromis et redistribue localement l'erreur de représentation sans modifier Survey/Scene.

Objectif : **maximiser la fidélité perceptive et architecturale sous contraintes LEGO réellement validées**.

La sélection ne doit pas être un simple score qui permet à un gain de détail de détruire une priorité supérieure. Une passe tardive ne doit pas dégrader un niveau supérieur au-delà d'une tolérance explicite.

Exemples : déplacer légèrement un trumeau pour faire tenir une vraie fenêtre LEGO peut être acceptable et doit être tracé ; faire disparaître la fenêtre ne l'est pas. Simplifier un garde-corps peut être nécessaire ; déplacer la terrasse du mauvais côté ne l'est pas. Une toiture constructible qui transforme un pignon peu pentu en triangle très aigu reste une mauvaise représentation. Une tuile sans chaîne d'appui/connexion n'est jamais acceptable parce qu'elle semble visuellement en place.

## Pipeline de référence

`preuves multi-vues → observations → correspondances entre vues → ArchitecturalSurvey → reconstruction topologique/géométrique → ArchitecturalScene → validation de vérité spatiale → importance architecturale → plan de représentation LEGO / choix de familles → réservation des empreintes des ancres → optimisation locale bornée → remplissage autour des ancres → détails → validation fidélité + support/connectivité/collisions → BrickModel → BOM / AssemblyPlan / InstructionPlan / BagPlan → viewer`

- `ArchitecturalSurvey` est l'autorité sémantique/observée.
- `ArchitecturalScene` est l'autorité métrique, géométrique et spatiale/topologique.
- Le futur plan de représentation LEGO explicite les choix de familles/assemblages avant remplissage.
- Les contraintes LEGO ne réécrivent jamais silencieusement Survey ou Scene.
- Les écarts introduits par la représentation LEGO doivent rester explicites et reliés, quand possible, à l'objet architectural source.
- L'inconnu reste inconnu.
- Les données privées restent hors du dépôt sans autorisation explicite.

## État réel actuel

### Acquis solides

- Survey et Scene possèdent des contrats déterministes et plusieurs validations inter-couches.
- Le pipeline Scene → LEGO → export → viewer fonctionne de bout en bout sur des références génériques.
- Les relations de plateforme, escalier, bâtiment et terrain ont plusieurs garde-fous de quantification et de fidélité.
- Les collapses intrinsèques d'un StairRun sont classés comme blockers de fidélité.
- Les ouvertures ont déjà des statuts de représentation et plusieurs garde-fous de non-disparition.
- La toiture à deux pans possède des garde-fous d'appui final, de proportion de pignon et de choix de famille de pente.
- Le viewer et le workflow déployé permettent désormais un contrôle humain réel du résultat.

### Régression produit confirmée par contrôle humain — ouverte

Le contrôle du cas réel a montré qu'une CI verte et un modèle techniquement généré ne suffisent pas. Les défauts observés incluent :

- terrasse et escalier insuffisamment fidèles dans leur géométrie/implantation ;
- portes et fenêtres mal représentées ou mal composées ;
- cheminée mal placée ;
- toiture/éléments de toiture pouvant sembler sans appui correct ;
- relations entre éléments caractéristiques insuffisamment protégées ;
- résultat global encore trop proche d'une coque remplie de briques et pas assez d'une interprétation LEGO architecturale.

Cette régression ne doit plus être traitée par retouches visuelles isolées. Le chantier prioritaire devient la chaîne de vérité spatiale → plan LEGO → constructibilité décrite par ADR-016 et l'issue BH-153.

## Prochaines briques de travail — ordre strict

### Brique 1 — vérité spatiale/topologique de la Scene — PRIORITÉ ACTIVE (BH-153)

Auditer les contrats et validateurs actuels puis combler les trous génériques nécessaires pour que les objets architecturaux ne soient plus seulement des coordonnées indépendantes.

À protéger selon les preuves : enveloppes, orientations, gauche/droite, avant/arrière, dessus/dessous, niveaux, contacts, connexions, supports, chevauchements, retraits, débords, traversées et ancrage à la bonne façade/surface/volume.

Critère de sortie : une relation certaine qui a une conséquence spatiale ne peut pas être marquée résolue si la géométrie la contredit ; un conflit bloquant empêche la projection LEGO avec un diagnostic explicite.

### Brique 2 — plan de représentation LEGO avant remplissage (BH-153)

Introduire progressivement une frontière explicite entre Scene et BrickModel pour choisir les familles/assemblages architecturaux réellement supportés avant l'infill.

Les fenêtres et portes sont des exemples prioritaires : le moteur choisit une solution LEGO compatible, connaît son empreinte, la réserve, puis résout les trumeaux/allèges/linteaux restants. Même principe pour toiture, cheminée, terrasse, garde-corps et escalier lorsque le vocabulaire le permet.

Critère de sortie : le remplissage ne peut plus dicter a posteriori la taille/position des ancres architecturales.

### Brique 3 — tolérances d'adaptation et résolution des conflits

Formaliser les invariants intouchables (côté, ordre, niveau, topologie, relations certaines) et les ajustements locaux autorisés. Toute redistribution doit être bornée, quantifiée et traçable sans mutation de Survey/Scene.

### Brique 4 — chaîne physique de support/connectivité

Étendre les validations existantes pour qu'une pièce ou un sous-assemblage ne soit accepté que s'il possède un support/une connexion modélisée appropriée. Distinguer proximité, contact, connectabilité, support et collision. À terme, vérifier la chaîne vers une structure porteuse.

Critère de sortie : une tuile, un plateau, un garde-corps ou un détail flottant devient un blocker déterministe avant export.

### Brique 5 — composition complète des ouvertures

Avec la planification d'empreintes en place, protéger rythme de façade, alignements, rapports largeur/hauteur, trumeaux et relations portes ↔ fenêtres ↔ terrasse/escalier. Les cadres/appuis/linteaux viennent ensuite.

### Brique 6 — silhouette, proportions et éléments caractéristiques

Verrouiller largeur/hauteur, étagement, pente, volumes secondaires, terrasse, escalier, cheminées, retraits/annexes et terrain sans laisser une optimisation locale dégrader l'identité.

### Brique 7 — détails architecturaux et finition de type set LEGO

Seulement après les portes précédentes : encadrements, appuis, linteaux, subdivisions réellement supportées, garde-corps détaillés, rives/faîtage, texture/composition des façades et autres détails qui donnent une finition de maquette architecturale plutôt qu'une voxelisation.

### Brique 8 — validation humaine du premier vrai rendu

Quand le pipeline génère une version où la maison est reconnaissable avant même d'examiner les petites briques et où les contrôles de support passent, demander une validation visuelle humaine sur : implantation des objets, silhouette, proportions, ouvertures, toiture et éléments caractéristiques.

Ce jalon précède l'optimisation fine de BOM/notice.

## Chantiers parallèles à ne pas confondre avec ce jalon

- BH-090 / round-trip humain Photos → Survey → Scene reste un jalon de validation externe ; ne pas inventer de données pour le fermer.
- SurveyAudit / SurveyCorrection restent bornés, diagnostiques et traçables ; ne pas les utiliser pour masquer une régression du moteur LEGO.
- SceneAudit reste conditionnel à la preuve d'un gain non redondant ; les nouveaux contrôles déterministes de topologie ne nécessitent pas de transformer SceneAudit en boucle IA.
- L'analyse multi-vues privée peut exploiter les photos fournies dans une session de travail, mais ces photos, leurs dérivés privés et les mesures exactes ne doivent pas être commis dans le dépôt sans autorisation explicite.

## Ce qui compte comme progression réelle

Une PR fusionnée ou un nombre de tests plus élevé n'est pas, seul, une progression produit.

Une progression réelle doit améliorer au moins un de ces axes sans dégrader les précédents :

- vérité architecturale et spatiale préservée ;
- reconnaissance visuelle ;
- fidélité métrique/proportionnelle ;
- représentation LEGO cohérente et planifiée ;
- constructibilité/validation physique ;
- reproductibilité et diagnostic ;
- expérience de validation dans le viewer.

Toute régression visuelle ou architecturale observée doit rester inscrite ici jusqu'à sa résolution.

## Données privées

Les photos de maison, PDF, Survey, Scene privés et mesures exactes privées ne doivent pas être ajoutés au dépôt sans autorisation explicite. Les régressions automatiques doivent rester génériques ou anonymisées.

## Instruction de reprise

> Lis `AI_START_HERE.md`, vérifie l'état réel de `main`, puis lis `PROGRESSION.md`. Reprends la première brique non résolue dans l'ordre indiqué. Ne relance pas un rendu réel avant d'avoir avancé sur la vérité spatiale, la planification LEGO et les portes de constructibilité décrites par ADR-016/BH-153.
