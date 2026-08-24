# Boldungo / BrickHouse — reprise immédiate de conversation

Date : 2026-08-24

> À lire **après `HANDOFF.md`**. Ce fichier décrit uniquement l'état le plus récent du benchmark 5 photos et le point exact de reprise. Si le code de `main` diverge, `main` reste la source de vérité.

## 1. Dépôt et URLs utiles

- dépôt : `ludodulac/lego-app`
- branche de vérité : `main`
- interface photo : `https://ludodulac.github.io/lego-app/photo.html`
- benchmark : `frontend/benchmarks/real-house-5/`
- les 5 JPEG originaux sont maintenant réellement présents dans ce dossier et sont chargeables via le bouton **« Charger la maison test — 5 photos »**.

## 2. Ce qui a été intégré récemment

- Logo Boldungo + texte d'accueil ajoutés au frontend sans Base64.
- Benchmark 5 photos chargeable directement depuis l'interface de test.
- PR #114 mergée : consigne de recouvrement entre photos et notion d'`overlap_anchors` ajoutées au workflow et au prompt topologique.
- Règle produit à conserver : une bonne séquence de photos doit garder un élément physique reconnaissable entre deux vues voisines (angle, fenêtre, terrasse, garde-corps, cheminée, toiture, etc.). Ces éléments servent d'ancres multi-vues. Une absence d'ancre ne doit jamais être compensée par une continuité inventée.

## 3. Ordre actuel du benchmark 5 photos

1. façade avant ;
2. côté droit ;
3. côté gauche ;
4. deuxième vue côté gauche / 3-4 ;
5. arrière / 3-4 arrière partiel.

Les labels restent des `capture_hint`, pas des vérités imposées à l'IA.

## 4. Test réel effectué

Le parcours a été exécuté manuellement :

`5 photos -> PDF externe -> analyse IA -> import bundle JSON -> validation Survey -> validation Scene -> build LEGO -> viewer`

Le PDF généré par l'interface contenait bien les 5 photos et les prompts actuels.

Le premier JSON produit par l'IA n'était pas conforme au contrat. Plusieurs corrections manuelles ont été nécessaires uniquement pour faire traverser le validateur :

- kinds Survey invalides (`dimension`, `secondary_volume`, `visibility`) ;
- rangs qualitatifs invalides (`facade_horizontal_rank`, `facade_vertical_rank`) ;
- `SourceInfo.kind="unknown"` invalide pour des métriques Scene ;
- `floors` manquant ;
- IDs Survey -> Scene non conservés ;
- observations d'ouvertures groupées alors que le validateur attend des objets physiques individuels ;
- pente Scene sans observation Survey `terrain` correspondante ;
- escalier non raccordé au sol selon le validateur ;
- convention de `facade_vertical_rank` inversée.

Important : **ne pas considérer le JSON corrigé manuellement comme une vérité architecturale ou un gold fixture**. Le but de ces corrections était de tester le pipeline et d'atteindre le viewer, pas d'établir une reconstruction fiable.

Le dernier état a finalement été accepté par Boldungo avec le message :

> `ArchitecturalScene valide et constructible. Étape suivante : cliquez sur « Construire cette proposition ».`

Puis la maquette LEGO a été construite et visualisée.

## 5. Résultat visuel obtenu : benchmark d'échec n°1

Le modèle est techniquement constructible, mais architecturalement insuffisant. Il faut conserver ce résultat comme **échec de fidélité**, pas comme succès.

Retour utilisateur précis sur le modèle :

- **toiture/pignon : échec majeur** : le rendu est ouvert / sans vraie toiture alors que les photos montrent clairement une toiture inclinée et un pignon ; auparavant le pipeline savait encore afficher un toit, donc rechercher une régression ;
- **façade avant** : la grande ouverture basse / porte d'atelier n'est pas correctement représentée ;
- **encadrements de fenêtres** : les bordures minérales visibles sur la façade avant manquent dans le rendu ;
- **terrasse côté gauche** : mauvaise emprise et mauvaise géométrie ; la vraie terrasse se prolonge beaucoup plus loin le long de la maison ;
- **escalier côté gauche** : mauvais emplacement, mauvaise longueur et mauvais matériau ; il est en béton, continue plus loin et dépasse vers l'arrière ;
- **ouvertures côté terrasse** : plusieurs ouvertures visibles manquent, notamment une porte / porte-fenêtre et une fenêtre au-dessus de la zone d'accès / en haut de l'escalier ;
- **côté droit** : fenêtre(s) mal positionnée(s) ;
- **vitrages** : le moteur a créé un aspect quadrillé / pavés alors que ce détail n'est pas prouvé pour toutes les fenêtres ; quand le style exact est incertain, utiliser un rendu neutre ou garder l'incertitude plutôt que d'inventer un motif ;
- **terrain** : la pente du côté droit est au moins présente, mais ce point positif ne compense pas les erreurs structurelles.

Le viewer a signalé des `fidelity_issues` sur la terrasse et l'escalier, mais **il n'a pas signalé l'absence catastrophique du toit comme une perte de fidélité suffisante**. Le message « valide et constructible » est donc trop permissif vis-à-vis de la fidélité architecturale.

## 6. Diagnostic principal

Le prochain travail ne doit PAS consister à retoucher encore le JSON à la main jusqu'à obtenir une jolie maison.

Le problème principal est en amont : **transmission de la vérité architecturale entre photos -> Survey -> Scene -> LEGO**.

Une Scene peut aujourd'hui être valide/constructible tout en ayant perdu des faits visuellement évidents. Il faut renforcer les invariants et tests de fidélité.

## 7. Priorités exactes de reprise

### Priorité A — toiture / pignon

C'est la première régression à traiter.

- vérifier le Survey généré pour savoir si le toit/pignon était encore présent et avec quelle certitude ;
- vérifier le passage Survey -> Scene ;
- vérifier le validateur Scene/Survey ;
- vérifier le build LEGO ;
- ajouter un test de régression : un toit/pignon certain dans le Survey ne doit jamais aboutir à un bâtiment ouvert sans toiture dans le viewer ;
- si la géométrie exacte du toit est inconnue, le système doit conserver l'existence du toit et signaler la géométrie incomplète plutôt que l'omettre silencieusement.

### Priorité B — inventaire d'ouvertures par façade

- chaque ouverture physique visible doit avoir un ID stable individuel dès le Survey ;
- ne pas regrouper plusieurs fenêtres dans une seule observation comme `front_openings` ;
- préserver comptes, façade, ordre horizontal/vertical et type avec certitudes séparées ;
- façade avant du benchmark : 6 ouvertures visibles ;
- côté droit : 2 ouvertures visibles ;
- côté gauche : il faut exploiter les vues 3/4 et les recouvrements pour conserver les ouvertures visibles près de la terrasse ;
- ne pas utiliser les valeurs métriques bricolées lors du test manuel comme vérité.

### Priorité C — terrasse et escalier multi-vues

- utiliser explicitement les `overlap_anchors` entre photos 3, 4 et 5 ;
- la terrasse commune à plusieurs vues doit être reconnue comme le même objet physique ;
- l'escalier visible doit conserver matériau et portée observables ;
- ne pas inventer de raccord caché ; si une portion n'est pas visible, garder `unknown`/incertain ;
- ne pas raccourcir une structure uniquement pour satisfaire le validateur de connectivité.

### Priorité D — fenêtres et détails architecturaux

- préserver les encadrements / surrounds observés ;
- ne pas transformer une fenêtre incertaine en pavés de verre ou faux quadrillage ;
- si le type exact n'est pas prouvé, choisir une représentation visuellement neutre et reporter l'incertitude ;
- les vraies fenêtres / portes distinctes doivent rester distinctes jusqu'au viewer.

### Priorité E — qualité du message de validation

Le système doit distinguer clairement :

- `schema_valid` ;
- `scene_survey_consistent` ;
- `constructible` ;
- `architecturally_faithful_enough_for_review`.

Une Scene sans toit alors que le toit est certain ne doit pas être présentée simplement comme « valide et constructible » sans alerte bloquante ou fidélité critique.

## 8. Fichiers à inspecter en premier

Toujours vérifier l'état réel de `main`, mais commencer ici :

- `HANDOFF.md`
- `NEXT_CONVERSATION.md` (ce fichier)
- `frontend/brickhouse-topology-prompt.txt`
- `frontend/brickhouse-survey-prompt.txt`
- `frontend/brickhouse-survey-to-scene-prompt.txt`
- `frontend/brickhouse-single-package.js`
- `frontend/benchmark-test.js`
- `frontend/benchmarks/real-house-5/manifest.json`
- `backend/brickhouse/survey/models.py`
- `backend/brickhouse/survey/validation.py`
- `backend/brickhouse/scene/models.py`
- `backend/brickhouse/scene/survey_validation.py`
- `backend/brickhouse/scene/survey_structure_guard.py`
- `backend/brickhouse/scene/projection.py`
- `backend/brickhouse/bricks/scene_architecture.py`
- `backend/brickhouse/bricks/roof.py`
- `backend/brickhouse/bricks/windows.py`
- `backend/brickhouse/bricks/facade_details.py`
- tests liés au Survey/Scene/toit/ouvertures/structures extérieures.

## 9. Règles de travail pour la prochaine conversation

- Ne pas demander à l'utilisateur de renvoyer les 5 photos : elles sont dans GitHub.
- Ne pas utiliser Base64 dans le dépôt pour les images.
- Ne pas modifier l'interface pour l'instant sauf si cela facilite strictement le test.
- Corriger une cause à la fois et ajouter un test de non-régression avant merge.
- Ne pas rendre le benchmark 5 photos artificiellement parfait avec des informations provenant d'autres photos ou de souvenirs hors benchmark.
- Les éléments invisibles doivent rester inconnus.
- Ne pas déclarer un succès sur la seule base du passage des validateurs.

## 10. Point exact de reprise

**Commencer par diagnostiquer la disparition de la toiture/pignon dans le dernier pipeline accepté.**

Objectif du prochain jalon :

1. déterminer précisément à quelle étape l'information de toit est perdue ;
2. corriger cette étape de manière générique ;
3. ajouter un test de régression utilisant le benchmark ou un fixture minimal générique ;
4. faire passer CI ;
5. merger ;
6. seulement ensuite relancer un test utilisateur 5 photos.

Après le toit, traiter l'inventaire d'ouvertures et le complexe terrasse/escalier.
