# Boldüngo / BrickHouse — progression

Dernière mise à jour : 2026-09-04

Ce fichier est la source unique de progression opérationnelle à consulter pour savoir où en est réellement le projet et quelles sont les prochaines briques de travail. Il ne remplace pas `PROJECT_PRINCIPLES.md`, les ADR, les contrats ou les tests. L'état réel de `main`, des PR/issues, de la CI et de Pages reste à revérifier avant toute action.

## Philosophie à préserver

La mission reste : transformer des preuves architecturales, notamment des photos, en une représentation structurée et traçable permettant de produire une maquette LEGO fidèle et des instructions de construction, sans inventer ce que les preuves ne permettent pas d'établir.

Ordre de priorité du résultat :

1. reconnaissance de la silhouette et des volumes ;
2. proportions architecturales ;
3. composition des ouvertures ;
4. éléments caractéristiques de la maison ;
5. détails architecturaux ;
6. traduction LEGO physiquement cohérente ;
7. BOM, montage, notice et viewer.

La géométrie LEGO ne doit jamais devenir plus importante que la fidélité architecturale. Une amélioration de placement de briques qui rend la maison moins reconnaissable est une régression produit.

## Pipeline de référence

`photos multi-vues → ArchitecturalSurvey → ArchitecturalScene → adaptation aux capacités LEGO → BrickModel → validation géométrique/assemblage → BOM / AssemblyPlan / InstructionPlan / BagPlan → viewer`

- `ArchitecturalSurvey` est l'autorité sémantique/observée.
- `ArchitecturalScene` est l'autorité métrique/géométrique.
- Les contraintes LEGO ne réécrivent jamais silencieusement Survey ou Scene.
- L'inconnu reste inconnu.
- Les données privées restent hors du dépôt sans autorisation explicite.

## État réel actuel

### Acquis solides

- Survey et Scene sont validés par contrats déterministes.
- Le pipeline Scene → LEGO → export → viewer fonctionne de bout en bout sur des références génériques.
- Les relations de plateforme, escalier, bâtiment et terrain ont plusieurs garde-fous de quantification et de fidélité.
- Les collapses intrinsèques d'un StairRun sont désormais classés comme blockers de fidélité.
- La CI publie un export riche générique `ArchitecturalScene → LEGO` comme artefact.
- GitHub Pages expose une prévisualisation du rich Scene dans le viewer existant.
- La CI et Pages étaient vertes après BH-122 au SHA `b438976afbf45cdad7eb43001f8a18c68d1c9cf9` au moment de cette mise à jour.

### Régression constatée le 2026-09-04

Le premier contrôle visuel humain du résultat riche a montré que le moteur est devenu plus propre sur certains placements LEGO mais moins fidèle architecturalement :

- perte importante de la composition des ouvertures ;
- grandes façades aveugles donnant un volume générique ;
- reconnaissance de la maison insuffisante ;
- toiture visuellement désolidarisée des murs sur certaines vues : pans flottants/décalés au lieu de reposer correctement sur les lignes d'appui ;
- terrasse/escalier présents mais insuffisants pour compenser la perte de l'identité architecturale.

Conclusion : le rendu actuel n'est pas une référence produit acceptable. Une CI verte ne suffit pas si le résultat architectural régresse.

## Prochaines briques de travail — ordre strict

### Brique 1 — rétablir le contrat de fidélité architecturale avant remplissage LEGO

Définir et tester explicitement que les éléments structurants de la Scene pilotent la représentation LEGO avant le remplissage des murs : silhouette, volumes, proportions, ouvertures et éléments caractéristiques.

Critère de sortie : une Scene possédant des ouvertures certaines ne peut pas produire silencieusement une façade pleine qui les fait disparaître.

### Brique 2 — corriger l'appui géométrique de la toiture

La toiture doit être dérivée du même repère final que les murs/pignons. Les lignes d'égout/appui, le faîtage, la pente et le débord doivent rester cohérents après quantification LEGO.

Ajouter une régression générique qui détecte un pan de toit censé reposer sur le bâtiment mais qui flotte, se décale ou se désolidarise de son host.

Critère de sortie : aucun pan de toiture supporté par le volume principal ne flotte visuellement au-dessus ou à côté de son appui final.

### Brique 3 — restaurer la composition des ouvertures

Les fenêtres et portes structurées dans la Scene doivent rester des ancres prioritaires. Le remplissage des murs doit se faire autour d'elles, pas l'inverse.

Priorité de reconnaissance : positions relatives, alignements horizontaux/verticaux, rapports de largeur/hauteur, rythmes de façade, puis détails de cadres/appuis/linteaux.

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
