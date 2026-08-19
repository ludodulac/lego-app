# BrickHouse — Idées & réflexions futures

Ce document sert de parking permanent pour les idées importantes qui ne doivent pas ralentir le développement du cœur du produit. Les idées restent visibles, classées et pourront être transformées en issues quand leur priorité arrivera.

## 1. Intérieurs des maisons — futur lointain

- Photos intérieures prises pièce par pièce ou étage par étage.
- Description textuelle alternative : pièces, cuisine, salon, chambres, sanitaires, escaliers, mobilier fixe.
- Futur `InteriorModel` séparé du `BuildingModel` extérieur.
- Gestion des portes intérieures, cloisons, circulations, escaliers, meubles et objets décoratifs.
- L'extérieur doit rester entièrement fonctionnel sans intérieur.

Référence : issue BH-FUTURE #52.

## 2. Architecture atypique et compréhension des formes

- Plusieurs volumes assemblés, extensions et décrochements.
- Maisons en L, U, formes biaisées, façades non symétriques, volumes arrondis quand une approximation LEGO est possible.
- Immeubles, appartements, maisons étroites, bâtiments industriels et architectures non résidentielles.
- Comprendre les proportions plutôt que forcer toute photo dans un gabarit de maison standard.
- Conserver pour chaque élément son origine : observé, fourni par l'utilisateur, inféré ou complété par défaut.

## 3. Toitures avancées

- Toit plat.
- Monopente.
- Toit à deux pans avec plusieurs pentes.
- Croupe, demi-croupe, mansarde et toitures multiples.
- Lucarnes, chiens-assis, fenêtres de toit.
- Cheminées, conduits, antennes, panneaux solaires, gouttières.
- Le toit doit toujours être structurellement connecté aux murs et/ou à une charpente simplifiée supportée.

## 4. Matériaux, textures et couleurs

- Reconnaître brique, pierre, crépi, bois, bardage, verre, métal, zinc, tuile, ardoise, etc.
- Séparer le matériau réel observé de son équivalent constructible en pièces.
- Gérer motifs, alternances de couleurs, murs en pierre apparente et colombages stylisés.
- Ne jamais afficher un matériau ou détail qui n'existe pas dans la BOM de la maquette finale.

## 5. Extérieurs et aménagements autour du bâtiment

Future couche possible `ExteriorModel` / `SiteModel`, indépendante du bâtiment principal :

- Terrasses bois ou minérales.
- Perrons et escaliers extérieurs.
- Balcons, auvents, vérandas et marquises.
- Murets, clôtures, portails et allées.
- Parterres de fleurs, jardinières, haies et végétation stylisée.
- Arbres, pelouse et relief simplifié.
- Pergolas, abris, garages et dépendances.
- Piscines et bassins lorsque le format de maquette le permet.

Référence : issue #53.

## 6. Formats et niveaux de fidélité

Deux axes doivent rester séparés :

### Format physique

- **Compact** — environ 32 tenons de largeur de référence ; souvenir / petit espace.
- **Standard** — environ 48 tenons ; choix recommandé par défaut.
- **Grand** — environ 64 tenons ; meilleure conservation des détails.

### Fidélité

- **Essentielle** — volumes, ouvertures et silhouette prioritaires ; moins de pièces.
- **Détaillée** — encadrements, matériaux, rebords, détails de toiture et architecture plus fidèle.

Le moteur devra pouvoir recommander automatiquement un format minimum quand un niveau de détail demandé est impossible à une échelle trop petite.

Référence : BH-038.

## 7. Fenêtres et façades

- Familles de vraies fenêtres constructibles : simples, quatre carreaux, hautes traditionnelles, jumelées, bow-window, etc.
- Cadres, vitrages, croisillons, appuis, linteaux et entourages.
- Choix automatique d'une famille selon la photo et selon le format/fidélité de la maquette.
- Toute pièce visuelle doit apparaître dans BrickModel, BOM et AssemblyPlan.

Référence : BH-037.

## 8. Notice et expérience de montage

- Caméra automatique choisie selon la façade ou la zone réellement travaillée à chaque étape.
- Zoom intelligent sur les nouvelles pièces.
- Étapes distinctes pour murs, ouvertures, détails, toiture et extérieurs.
- Export PDF de qualité impression.
- À terme, possibilité d'impression papier ou de commande d'un kit de pièces.

## 9. Questions ouvertes à conserver

- Jusqu'où privilégier réalisme vs robustesse/constructibilité ?
- Faut-il proposer un mode « exposition » et un mode « jeu » plus solide ?
- Comment estimer le prix du modèle avant génération complète ?
- Comment gérer les éléments cachés ou non photographiés sans créer de fausse certitude ?
- Comment permettre des corrections manuelles simples sans transformer BrickHouse en logiciel de CAO ?
- Comment gérer plus tard le partage public/privé de modèles créés par les utilisateurs ?

---

Principe directeur : **ne jamais laisser une idée future bloquer le prochain jalon utile du produit.** Lorsqu'une idée devient prioritaire, elle doit être extraite de ce document vers une issue dédiée avec critères d'acceptation et tests.
