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
- BH-125 est fusionné : chaque fenêtre architecturale générée possède désormais un statut explicite de représentation (`validated_assembly`, `joinery_free_glazing`, `void_only`). Une composition connue mais non représentable par le vocabulaire LEGO validé produit le blocker `lego_architectural_window_unrepresented` au lieu d'être considérée comme une façade aveugle réussie. Les subdivisions non supportées ne sont pas inventées.
- La CI de BH-125 était verte sur la PR #424 avant fusion ; `main` est au SHA `0088d7b0f80fea8bc1c39702d70dcd76f23df71f` au moment de cette mise à jour.

### Régression constatée le 2026-09-04 — encore ouverte

Le premier contrôle visuel humain du résultat riche a montré que le moteur est devenu plus propre sur certains placements LEGO mais moins fidèle architecturalement :

- perte importante de la composition visuelle des ouvertures ;
- grandes façades aveugles ou trop génériques ;
- reconnaissance de la maison insuffisante ;
- toiture visuellement désolidarisée des murs sur certaines vues : pans flottants/décalés au lieu de reposer correctement sur les lignes d'appui ;
- proportions du pignon/toiture susceptibles d'être trop hautes/aiguës par rapport à la preuve photographique ;
- terrasse/escalier présents mais insuffisants pour compenser la perte de l'identité architecturale.

BH-125 empêche désormais qu'une ouverture connue et non représentable soit silencieusement déclarée réussie. Cela ferme le contrat de sécurité de la Brique 1, mais ne suffit pas encore à restaurer toute la composition visuelle du rendu. La régression globale reste donc ouverte.

Conclusion : le rendu actuel n'est pas une référence produit acceptable. Une CI verte ne suffit pas si le résultat architectural régresse.

## Prochaines briques de travail — ordre strict

### Brique 1 — contrat de fidélité architecturale avant remplissage LEGO — RÉSOLUE AU NIVEAU OUVERTURES

Les ouvertures connues sont désormais des ancres explicites : le raster de mur conserve le vide, les solutions LEGO validées sont choisies avant le remplissage, les parties générées gardent leur provenance d'ouverture et une composition connue non représentable devient un blocker de fidélité au lieu de disparaître silencieusement.

Ce contrat doit rester la règle pour les futures ancres architecturales, mais le critère de sortie initial est rempli.

### Brique 2 — corriger l'appui géométrique et la proportion de la toiture — EN COURS

La toiture doit être dérivée du même repère final que les murs/pignons. Les lignes d'égout/appui, le faîtage, la pente et le débord doivent rester cohérents après quantification LEGO.

Le contrôle doit distinguer deux problèmes :

- **contact/appui** : un pan censé être porté par le bâtiment ne peut pas flotter, se décaler ou perdre sa ligne d'appui ;
- **proportion** : le choix d'une famille de pente LEGO ne doit pas produire un pignon manifestement plus haut/aigu que l'architecture source sans diagnostic explicite ni recherche d'une solution de représentation meilleure.

Ajouter des régressions génériques qui couvrent la continuité toiture-host et le rapport hauteur de pignon / demi-portée après quantification.

Critère de sortie : aucun pan de toiture supporté par le volume principal ne flotte visuellement au-dessus ou à côté de son appui final, et une quantification de pente qui déforme fortement le pignon n'est pas silencieusement acceptée.

### Brique 3 — restaurer la composition complète des ouvertures

Les fenêtres et portes structurées dans la Scene doivent rester des ancres prioritaires. Le remplissage des murs doit se faire autour d'elles, pas l'inverse.

Priorité de reconnaissance : positions relatives, alignements horizontaux/verticaux, rapports de largeur/hauteur, rythmes de façade, puis détails de cadres/appuis/linteaux.

BH-125 fournit le contrat de non-disparition. Cette brique doit maintenant améliorer la fidélité compositionnelle réelle lorsque plusieurs solutions LEGO sont possibles.

Critère de sortie : la façade reste identifiable par sa composition même sans textures ni petits détails.

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
