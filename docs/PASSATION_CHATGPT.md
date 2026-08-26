# PASSATION CHATGPT — Boldungo / BrickHouse

Dernière mise à jour : 2026-08-26
Dépôt : `ludodulac/lego-app`

## Instruction à la prochaine conversation

Commence par lire ce fichier en entier, puis inspecte l’état réel du dépôt et des PR avant toute modification. Ne suppose pas que les états CI décrits ici sont encore actuels.

## Objectif produit

Boldungo doit transformer plusieurs photos d’une maison réelle en une reconstruction architecturale prudente, puis en maquette LEGO et notice de montage. La règle centrale est : **ne jamais inventer une géométrie simplement pour obtenir un rendu complet**. Il faut distinguer ce qui est observé, déduit et inconnu, recouper les vues, conserver les contradictions/incertitudes, puis seulement convertir en géométrie et en LEGO.

## Cas de référence BrickHouse

Les fixtures principales sont :
- `tests/fixtures/brickhouse_survey_current.json`
- `tests/fixtures/brickhouse_scene_current.json`
- l’analyse visuelle indépendante ajoutée récemment dans les fixtures/tests (la retrouver par recherche `independent` / `brickhouse`).

Une analyse indépendante des cinq photos a confirmé plusieurs faiblesses des anciennes hypothèses. Les corrections déjà fusionnées ont notamment supprimé la plage de toit arbitraire `10–35°`, supprimé la direction de pente `rear` considérée comme résolue, réduit la certitude sur les trois étages et sur certaines relations cachées. Le principe à conserver : une inconnue doit rester inconnue jusqu’à preuve suffisante.

## État du visualiseur architectural

Le visualiseur est dans `frontend/scene-viewer.js`. Il affiche les volumes, ouvertures et certains éléments extérieurs avant la conversion LEGO.

Le contrôle visuel utilisateur a révélé notamment :
- la maison est encore trop abstraite et ne ressemble pas assez aux cinq photos ;
- la toiture avait un bug `null -> 0` côté JavaScript ;
- la terrasse doit intégrer correctement sa structure observée (plancher, poteau(x), renforts diagonaux, garde-corps), sans inventer coordonnées/nombre non établis ;
- l’escalier doit occuper une vraie profondeur extérieure et ne pas être comprimé contre la maison ;
- certaines ouvertures / porte-fenêtre / porte d’entrée doivent être mieux raccordées entre vues ;
- la pente du terrain/rue côté droit est observée mais pas métriquement mesurée ; ne pas dessiner une pente numérique arbitraire ;
- les cheminées/vestiges dont l’appartenance à BrickHouse est ambiguë doivent rester ambigus.

## Bug toiture en cours

Une correction existe pour empêcher JavaScript de transformer une pente `null` en `0°`. Elle exige une valeur numérique non-null et une direction connue avant de dessiner un plan de toiture. Un test de régression a été ajouté dans `tests/test_architectural_scene_preview.py`.

Ancienne PR : #186 `Keep unknown BrickHouse roof unknown in 3D preview`.
Cette PR a été fermée sans fusion car sa CI #950 est restée `queued` sans aucun job créé.

Branche de remplacement : `fix/scene-preview-unknown-roof-v2`
PR de remplacement : #187
Head attendu au moment de cette passation : `7256b96553044120a9343780786fe6bc8395fb24`

IMPORTANT : juste après la création de #187, aucune exécution CI n’était encore visible. Vérifier l’état réel avant d’agir.

## Diagnostic GitHub Actions

Workflow : `.github/workflows/ci.yml`
Il contient :
- `on.push.branches: [main]`
- `on.pull_request`
- un job `test` sur `ubuntu-latest`
- pas de règle `concurrency`.

Pour #186, le run CI #950 est resté `queued` et sa liste de jobs était vide. Un commit vide a ensuite été poussé sur la branche, mais aucune nouvelle exécution n’a été créée. Cela suggère un problème de déclenchement/approbation/contexte Actions plutôt qu’un test lent.

Point à connaître : les PR ou mises à jour créées par automatisation peuvent avoir des comportements particuliers de déclenchement/approbation GitHub Actions. Ne modifie pas `ci.yml` sans preuve. Vérifie d’abord #187, les check-runs, les éventuelles demandes d’approbation et les règles du dépôt.

## Branche terrain

Une branche `feat/scene-preview-terrain` a été créée depuis `main`. Le modèle `Terrain` supporte déjà des profils par façade avec `start_elevation`, `end_elevation`, `outward_extent`. Dans la Scene BrickHouse actuelle, la pente côté droit est observée mais ces valeurs métriques restent `null`.

Bonne direction : permettre au visualiseur de signaler graphiquement/sémantiquement « pente observée mais non métrée » sans fabriquer une surface inclinée chiffrée. Une vraie surface inclinée ne doit être générée que lorsque les données métriques existent.

## Méthode de travail souhaitée

Travailler par petites PR isolées :
1. identifier un défaut précis ;
2. corriger sans ajouter d’hypothèse non prouvée ;
3. ajouter un test de régression ;
4. attendre/vérifier CI ;
5. fusionner seulement quand les contrôles sont verts ;
6. passer au défaut suivant.

Priorités après résolution du blocage CI :
1. fusionner la correction `null -> 0` si validée ;
2. représentation honnête du terrain non métré ;
3. enrichir le passage observations -> objets structurés pour terrasse/supports/renforts/escalier/ouvertures ;
4. refaire un aperçu 3D BrickHouse ;
5. demander à l’utilisateur un nouveau contrôle visuel seulement quand le rendu apporte réellement quelque chose ;
6. revenir ensuite vers la représentation LEGO, pas avant que la géométrie architecturale soit suffisamment cohérente.

## Préférence utilisateur importante

L’utilisateur veut que le travail continue de façon autonome autant que possible et qu’on ne lui demande d’intervenir que lorsqu’une action concrète de sa part est réellement nécessaire. Il souhaite également un glossaire lorsqu’un nouveau terme technique est introduit, sans répéter indéfiniment les termes déjà expliqués.

## Première action recommandée pour la prochaine conversation

1. Lire ce fichier.
2. Lire `tests/fixtures/brickhouse_scene_current.json`, `tests/fixtures/brickhouse_survey_current.json`, `.github/workflows/ci.yml`, `frontend/scene-viewer.js` et `tests/test_architectural_scene_preview.py`.
3. Inspecter PR #187 et ses workflows/checks.
4. Si une approbation manuelle GitHub Actions est requise, le dire clairement à l’utilisateur avec l’action exacte à effectuer. Sinon diagnostiquer le déclenchement avant toute modification de workflow.
5. Reprendre ensuite la séquence de petites PR ci-dessus.
