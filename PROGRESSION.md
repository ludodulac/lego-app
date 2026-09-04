# Boldüngo / BrickHouse — progression

Dernière mise à jour : 2026-09-04

Ce fichier est la source unique de progression opérationnelle à consulter pour savoir où en est réellement le projet et quelles sont les prochaines briques de travail. Il ne remplace pas `PROJECT_PRINCIPLES.md`, les ADR, les contrats ou les tests. L'état réel de `main`, des PR/issues, de la CI et de Pages reste à revérifier avant toute action.

## Philosophie à préserver

La mission reste : transformer des preuves architecturales, notamment des photos, en une représentation structurée et traçable permettant de produire une maquette LEGO fidèle et des instructions de construction, sans inventer ce que les preuves ne permettent pas d'établir.

Ordre de priorité du résultat :

1. reconnaissance de la silhouette et des volumes ;
2. proportions architecturales ;
3. composition des ouvertures ;
4. relations spatiales et éléments caractéristiques de la maison ;
5. matériaux/couleurs lorsqu'ils sont établis ;
6. détails architecturaux ;
7. exactitude locale du choix/placement des briques.

La géométrie LEGO ne doit jamais devenir plus importante que la fidélité architecturale. Une amélioration de placement de briques qui rend la maison moins reconnaissable est une régression produit.

## Cadre de décision — les quatre vérités

Le moteur doit maintenir quatre niveaux distincts et traçables :

1. **Vérité architecturale — qu'est réellement la maison ?** Les photos et autres preuves établissent volumes, orientations, niveaux, toiture, ouvertures, terrasse, escalier, cheminées, terrain et relations. L'incertitude reste explicite et cette vérité ne se déforme pas pour faciliter le LEGO.
2. **Vérité du catalogue LEGO — quelles pièces le moteur sait-il réellement utiliser ?** Dimensions, orientations, familles, rôles architecturaux et capacités de connexion doivent venir d'un vocabulaire validé. Une pièce ou subdivision non connue ne doit pas être inventée.
3. **Vérité constructive — est-ce réellement assemblable ?** Contacts, tenons/tubes, supports, collisions, gravité, continuité des murs, appui de toiture, stabilité et ordre d'assemblage sont des contraintes de faisabilité, pas des objectifs esthétiques facultatifs.
4. **Vérité de représentation — quel compromis LEGO conserve le mieux l'architecture ?** Lorsque le catalogue ne correspond pas exactement au réel, le moteur choisit le meilleur compromis et redistribue localement l'erreur de représentation sans modifier Survey/Scene.

Objectif : **maximiser la fidélité perceptive et architecturale sous contraintes LEGO réellement validées**.

La sélection ne doit pas être un simple score qui permet à un gain de détail de détruire une priorité supérieure. Le comportement cible est hiérarchique/gardé : silhouette → proportions → ouvertures → relations/éléments caractéristiques → matériaux → détails → exactitude locale des briques. Une passe tardive ne doit pas dégrader un niveau supérieur au-delà d'une tolérance explicite.

Exemples de coût d'erreur : déplacer légèrement un trumeau pour faire tenir une vraie fenêtre LEGO peut être acceptable et doit être tracé ; faire disparaître la fenêtre ne l'est pas. Simplifier un garde-corps peut être nécessaire ; déplacer la terrasse du mauvais côté ne l'est pas. Une toiture constructible qui transforme un pignon peu pentu en triangle très aigu reste une mauvaise représentation.

## Pipeline de référence

`preuves multi-vues → observations → correspondances entre vues → ArchitecturalSurvey → topologie/géométrie → ArchitecturalScene → importance architecturale → recherche de solutions LEGO → optimisation relative → remplissage autour des ancres → détails → validations de fidélité/constructibilité → BrickModel → BOM / AssemblyPlan / InstructionPlan / BagPlan → viewer`

- `ArchitecturalSurvey` est l'autorité sémantique/observée.
- `ArchitecturalScene` est l'autorité métrique/géométrique.
- Les contraintes LEGO ne réécrivent jamais silencieusement Survey ou Scene.
- Les écarts introduits par la représentation LEGO doivent rester explicites et, quand possible, reliés à l'objet architectural source.
- L'inconnu reste inconnu.
- Les données privées restent hors du dépôt sans autorisation explicite.

## État réel actuel

### Acquis solides

- Survey et Scene sont validés par contrats déterministes.
- Le pipeline Scene → LEGO → export → viewer fonctionne de bout en bout sur des références génériques.
- Les relations de plateforme, escalier, bâtiment et terrain ont plusieurs garde-fous de quantification et de fidélité.
- Les collapses intrinsèques d'un StairRun sont classés comme blockers de fidélité.
- La CI publie un export riche générique `ArchitecturalScene → LEGO` comme artefact.
- GitHub Pages expose une prévisualisation du rich Scene dans le viewer existant.
- **BH-125** : chaque fenêtre architecturale générée possède un statut explicite de représentation (`validated_assembly`, `joinery_free_glazing`, `void_only`). Une composition connue mais non représentable produit le blocker `lego_architectural_window_unrepresented` au lieu d'être considérée comme une façade aveugle réussie. Les subdivisions non supportées ne sont pas inventées.
- **BH-126** : la toiture à deux pans est revalidée après translation dans le repère final du `BrickModel`. Les deux lignes d'égout doivent encore toucher les limites finales du bâtiment et rester au niveau supérieur du mur ; un pan déplacé ou flottant est rejeté. Le débord architectural déclaré est conservé.
- **BH-127** : la fidélité du pignon n'est plus jugée seulement par l'écart angulaire. Le moteur mesure la variation de hauteur de pignon pour une même demi-portée via le rapport montée/course. Une déformation matérielle devient un warning et une déformation sévère un blocker.
- **BH-128** : le choix de famille de pente LEGO privilégie désormais la fidélité montée/course (`tan(pitch)`) avant la proximité en degrés. Au voisinage d'une frontière de catalogue, le moteur choisit donc la pièce qui conserve le mieux la proportion du pignon plutôt que celle qui gagne seulement quelques dixièmes de degré.
- Les CI des PR #427, #429 et #431 étaient vertes avant fusion.
- `main` est au SHA `1ae1922bce7b39840447a0633d40cf6fd3ac8f6f` au moment de cette mise à jour.

### Régression constatée le 2026-09-04 — encore ouverte

Le premier contrôle visuel humain du résultat riche a montré que le moteur est devenu plus propre sur certains placements LEGO mais moins fidèle architecturalement :

- perte importante de la composition visuelle des ouvertures ;
- grandes façades aveugles ou trop génériques ;
- reconnaissance de la maison insuffisante ;
- toiture visuellement désolidarisée des murs sur certaines vues ;
- proportions du pignon/toiture susceptibles d'être trop hautes/aiguës ;
- terrasse/escalier présents mais insuffisants pour compenser la perte de l'identité architecturale.

Les contrats BH-125 à BH-128 ferment maintenant plusieurs voies de régression silencieuse : disparition d'une fenêtre connue, toiture perdant son appui final, pignon fortement déformé sans diagnostic et mauvais choix de pente autour d'une frontière de catalogue.

Ils ne démontrent toutefois pas encore que le rendu riche est redevenu suffisamment reconnaissable. La régression globale reste ouverte jusqu'à un nouveau contrôle visuel sur un rendu réellement amélioré.

Conclusion : une CI verte reste nécessaire mais n'est pas suffisante si le résultat architectural régresse.

## Prochaines briques de travail — ordre strict

### Brique 1 — contrat de fidélité architecturale avant remplissage LEGO — RÉSOLUE AU NIVEAU OUVERTURES

Les ouvertures connues sont des ancres explicites : le raster de mur conserve le vide, les solutions LEGO validées sont choisies avant le remplissage, les parties générées gardent leur provenance d'ouverture et une composition connue non représentable devient un blocker de fidélité au lieu de disparaître silencieusement.

### Brique 2 — appui géométrique et proportion de la toiture — RÉSOLUE AU NIVEAU DU CONTRAT

BH-126 impose l'appui dans les coordonnées finales. BH-127 mesure la déformation réelle du pignon. BH-128 choisit la famille de pente qui minimise cette déformation avant l'écart angulaire.

Critère atteint au niveau moteur : un pan supporté ne peut plus perdre silencieusement son appui final, et une quantification de pente qui déforme le pignon est soit mieux évitée par le choix de famille, soit diagnostiquée avec une sévérité explicite.

Ce statut ne vaut pas validation photographique finale : la toiture devra encore être revue dans le prochain rendu humain.

### Brique 3 — restaurer la composition complète des ouvertures — EN COURS

Les fenêtres et portes structurées doivent rester des ancres prioritaires. Le remplissage des murs doit se faire autour d'elles, pas l'inverse.

Priorité de reconnaissance :

- positions relatives et ordre gauche/droite ;
- alignements horizontaux et verticaux ;
- rythme des centres et des espaces libres entre ouvertures ;
- rapports largeur/hauteur ;
- relation portes ↔ fenêtres ↔ terrasse/escalier ;
- seulement ensuite cadres, appuis et linteaux.

BH-105/BH-107 conservent déjà les centres relatifs X/Z lors de l'ancrage conjoint et BH-125 garantit la non-disparition. Le prochain travail doit mesurer puis protéger explicitement le **rythme de façade** lorsque les dimensions des vraies pièces LEGO changent les largeurs d'ouverture : conserver seulement les centres ne suffit pas si les trumeaux/espaces libres deviennent visuellement faux.

Critère de sortie : la façade reste identifiable par sa composition même sans textures ni petits détails, et une optimisation locale de taille/position ne peut pas dégrader fortement son rythme sans diagnostic ou recherche d'une meilleure solution.

### Brique 4 — verrouiller silhouette et proportions à l'échelle LEGO

Auditer la quantification globale pour éviter qu'une optimisation locale de briques déforme les rapports principaux : largeur/hauteur, étagement, pente de toiture et positions relatives des volumes.

Les ajustements LEGO doivent rester des décisions de représentation explicites ; la vérité métrique Scene reste immuable.

### Brique 5 — éléments caractéristiques

Une fois silhouette/proportions/ouvertures stables, consolider les objets qui donnent son caractère au bâtiment : plateforme/terrasse, escalier, cheminées, retraits, annexes et terrain lorsqu'ils sont établis par la Scene.

Ne jamais inventer un élément ou une dimension pour embellir le résultat.

### Brique 6 — détails architecturaux

Seulement après les cinq briques précédentes : cadres, retraits, appuis, linteaux, entourages, subdivisions de fenêtres lorsque le vocabulaire LEGO les représente réellement.

### Brique 7 — qualité physique LEGO

Poursuivre collisions, contacts, supports, connecteurs, stabilité et choix de pièces sans sacrifier les ancres architecturales précédentes.

### Brique 8 — validation humaine du premier vrai rendu

Quand le pipeline génère une version où la maison est reconnaissable avant même d'examiner les briques, demander une validation visuelle humaine sur : silhouette, proportions, ouvertures, toiture et éléments caractéristiques.

Ce jalon précède l'optimisation fine de BOM/notice.

## Chantiers parallèles à ne pas confondre avec ce jalon

- BH-090 / round-trip humain Photos → Survey → Scene reste un jalon de validation externe ; ne pas inventer de données pour le fermer.
- SurveyAudit / SurveyCorrection restent bornés, diagnostiques et traçables ; ne pas les utiliser pour masquer une régression du moteur LEGO.
- SceneAudit reste HOLD tant qu'un gain non redondant n'est pas démontré.
- L'analyse multi-vues privée peut exploiter les photos fournies dans une session de travail, mais ces photos, leurs dérivés privés et les mesures exactes ne doivent pas être commis dans le dépôt sans autorisation explicite.

## Ce qui compte comme progression réelle

Une PR fusionnée ou un nombre de tests plus élevé n'est pas, seul, une progression produit.

Une progression réelle doit améliorer au moins un de ces axes sans dégrader les précédents :

- vérité architecturale préservée ;
- reconnaissance visuelle ;
- fidélité métrique/proportionnelle ;
- représentation LEGO cohérente ;
- constructibilité/validation physique ;
- reproductibilité et diagnostic ;
- expérience de validation dans le viewer.

Toute régression visuelle ou architecturale observée doit être inscrite ici jusqu'à sa résolution.

## Données privées

Les photos de maison, PDF, Survey, Scene privés et mesures exactes privées ne doivent pas être ajoutés au dépôt sans autorisation explicite. Les régressions automatiques doivent rester génériques ou anonymisées.

## Instruction de reprise

> Lis `AI_START_HERE.md`, vérifie l'état réel de `main`, puis lis `PROGRESSION.md`. Reprends la première brique non résolue dans l'ordre indiqué, en privilégiant toujours la fidélité architecturale avant l'optimisation LEGO.
