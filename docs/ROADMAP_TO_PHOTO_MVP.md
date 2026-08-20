# BrickHouse — roadmap canonique vers le MVP photo

Ce document est la référence de reprise du projet. Le but n'est pas de polir indéfiniment une sous-partie : il est d'atteindre un parcours réel et testable **photos -> compréhension architecturale -> maquette LEGO constructible -> viewer/BOM/notice**.

## 1. But produit

À partir de plusieurs photos d'un bâtiment réel, BrickHouse doit :

1. comprendre les volumes, proportions, ouvertures et toiture visibles ;
2. séparer clairement ce qui est observé, fourni par l'utilisateur, inféré ou estimé ;
3. poser des questions uniquement lorsque l'incertitude peut modifier sensiblement la maquette ;
4. produire un `BuildingModel` éditable et validé ;
5. convertir ce modèle en une construction LEGO cohérente et réellement constructible ;
6. produire le `BrickModel`, la BOM, le viewer 3D et une notice pratique ;
7. permettre plusieurs formats physiques de maquette et plusieurs niveaux de fidélité.

## 2. Ce qui est déjà en place

### Modèle architectural
- `BuildingModel` paramétrique avec volumes, façades, ouvertures, toit et provenance des informations.
- configurateur manuel utilisable comme référence et comme solution de correction.

### Moteur LEGO
- conversion métrique -> tenons ;
- murs et appareillage ;
- toit à deux pans avec familles de pente ;
- pignons ;
- BrickModel canonique ;
- BOM déterministe ;
- premières familles de vraies fenêtres cadre + vitrage ;
- détails de façade constructibles ;
- formats Compact / Standard / Grand ;
- fidélité Essentielle / Détaillée enregistrée dans le projet.

### Sorties
- viewer 3D ;
- lecture par étapes ;
- export BOM CSV ;
- notice imprimable ;
- étapes courtes, phases, sachets virtuels, zooms, rotations, sous-assemblages de fenêtres.

### Infrastructure
- frontend GitHub Pages ;
- backend Render ;
- API `/build` ;
- révision moteur exposée ;
- CI couvrant le pipeline de référence.

### Vision déjà codée
- page d'upload 1 à 6 photos ;
- endpoint `/api/v1/analyze-photos` ;
- provider vision structuré ;
- `PhotoAnalysisResult` avec confiance, hypothèses et questions ;
- réinjection des réponses utilisateur ;
- passage direct du BuildingModel photo vers `/build`.

## 3. Chemin critique actuel

### P0 — rendre le MVP photo testable
- exposer les capacités réelles du serveur ;
- empêcher l'interface de prétendre analyser si la vision n'est pas activée ;
- valider taille/type/nombre de photos avant envoi ;
- tester automatiquement `photos -> BuildingModel -> /build -> BrickExportBundle` avec provider simulé ;
- activer un provider vision réel sur l'environnement de test ;
- faire un premier essai avec une maison simple bien photographiée.

### P1 — boucle de correction après premiers essais
- comparer photos / BuildingModel / rendu LEGO ;
- corriger les erreurs de proportions et d'ouvertures ;
- améliorer les questions de clarification ;
- stabiliser l'échelle avec une mesure connue quand disponible ;
- empêcher toute géométrie non supportée de produire silencieusement une fausse reconstruction.

### P2 — généraliser l'architecture
Après validation du flux simple :
- plusieurs volumes ;
- extensions et garages ;
- toits plats, monopentes, croupes et combinaisons ;
- cheminées et lucarnes ;
- architectures asymétriques et formes atypiques.

### P3 — fidélité architecturale et extérieurs
Après robustesse géométrique :
- familles de fenêtres supplémentaires ;
- matériaux et textures comme information de choix de pièces/couleurs ;
- corniches, rebords, entourages ;
- terrasses, murets, parterres, végétation et autres éléments extérieurs.

### P4 — intérieur
À conserver comme axe futur distinct : plans/niveaux, pièces intérieures, mobilier et circulation. Ne doit pas bloquer le MVP extérieur photo.

## 4. Règles de développement

- Le chemin critique photo a priorité sur le polish de la notice jusqu'aux premiers essais réels.
- Une pièce visible dans le viewer doit correspondre à une pièce du BrickModel/BOM ; pas de faux détail graphique servant à masquer une faiblesse du moteur.
- Une information non visible sur les photos ne doit jamais être déclarée « observée ».
- Une architecture non supportée doit être signalée ou simplifiée explicitement, jamais inventée silencieusement.
- Toute modification structurelle doit être couverte par la CI avant fusion dans `main`.
- Les idées non indispensables au MVP vont dans `docs/IDEAS_FUTURE.md` et ne détournent pas le chemin critique.

## 5. Définition de « premier MVP photo réussi »

Le MVP photo est considéré atteint lorsqu'un utilisateur peut :

1. ouvrir la page Photo ;
2. envoyer plusieurs vraies vues d'une maison simple ;
3. recevoir une proposition architecturale avec confiance/hypothèses/questions ;
4. corriger ou confirmer les points importants ;
5. cliquer sur « Construire cette proposition » ;
6. obtenir le viewer 3D de cette même maison ;
7. ouvrir sa BOM et sa notice ;
8. constater que le résultat conserve correctement proportions générales, toit, façades et ouvertures principales.

Ce jalon vient **avant** l'élargissement massif des styles architecturaux et des détails décoratifs.
