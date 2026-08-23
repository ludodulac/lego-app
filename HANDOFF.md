# BrickHouse — Passation de conversation

Dernière mise à jour : 2026-08-23

## 1. But du projet

BrickHouse doit reconstruire un bâtiment réel à partir de plusieurs photographies, puis convertir cette reconstruction en maquette LEGO.

Le système doit fonctionner en plusieurs étapes conceptuelles :
1. comprendre les vues et leur topologie ;
2. reconnaître les mêmes objets d'une photo à l'autre ;
3. établir un relevé architectural fiable ;
4. reconstruire une scène métrique cohérente ;
5. contrôler les relations géométriques ;
6. traduire cette scène en géométrie LEGO ;
7. présenter un parcours utilisateur simple.

Le point clé est que l'IA ne doit PAS analyser les photos indépendamment. Elle doit raisonner multi-vues et reconnaître les mêmes éléments lorsqu'ils réapparaissent : fenêtres, portes, terrasse, escalier, angles, toiture, terrain, murs secondaires, etc.

## 2. Principe de fiabilité

La hiérarchie de reconstruction doit rester stricte :

1. topologie et correspondances entre vues ;
2. nombre exact d'ouvertures par pan ;
3. identité/type des ouvertures ;
4. ordre et alignements ;
5. position ;
6. dimensions/proportions ;
7. structures extérieures ;
8. terrain ;
9. détails architecturaux ;
10. traduction LEGO.

Une étape plus basse ne doit jamais modifier un fait validé plus haut simplement pour faciliter le rendu LEGO.

Exemple : si le Survey prouve trois ouvertures sur une façade, la Scene ou le moteur LEGO ne doit pas en supprimer une pour faire rentrer un escalier.

## 3. Règles générales importantes

- Ne jamais compléter automatiquement une zone occultée.
- Ne jamais inventer une ouverture derrière un bâtiment, un arbre ou un obstacle.
- Ne jamais modifier gauche/droite par convention implicite.
- Le repère canonique est : x = gauche→droite vu de face, y = avant→arrière, z = bas→haut.
- Une porte en hauteur peut réellement donner dans le vide. Ne jamais inventer balcon, terrasse, escalier ou palier simplement pour « expliquer » une porte.
- Une structure extérieure complexe doit être décomposée en primitives rectilignes simples reliées entre elles.
- Les matériaux et traitements de bord doivent être structurés dans les données, pas déduits uniquement de texte libre.
- Les corrections doivent être génériques et réutilisables, jamais codées spécialement pour la maison test.

## 4. Dépôt

Repository : `ludodulac/lego-app`

Toujours inspecter le code réel dans GitHub avant de modifier quoi que ce soit. Ce fichier est une passation, pas une source de vérité absolue sur l'état courant du code.

## 5. Maison test actuelle

Cette maison sert de cas de validation. Les règles du moteur doivent rester génériques.

Affectation des photos connue lors des derniers tests :
- photo 1 : façade avant ;
- photo 2 : côté droit ;
- photo 3 : côté gauche ;
- photo 4 : côté gauche rapproché ;
- photo 5 : principalement arrière, avec encore des éléments du côté gauche visibles autour du coin.

Inventaire d'ouvertures actuellement verrouillé pour le corps principal :
- avant : 6 ;
- droite : 2 ;
- gauche : 3 ;
- arrière : 0.

Le dernier rendu correct avait enfin supprimé le miroir gauche/droite et respectait ces comptes.

La façade arrière ne doit pas recevoir de fenêtre inventée.

## 6. Façade avant

Attendus connus :
- quatre grandes fenêtres principales organisées en deux colonnes ;
- une petite ouverture basse à gauche ;
- une grande ouverture vitrée basse à droite.

Les fenêtres doivent conserver leurs axes verticaux et leurs proportions relatives.

Un ancien défaut majeur était l'utilisation de briques de mur comme meneaux/traverses au milieu des fenêtres. Ce comportement doit rester supprimé.

## 7. Côté droit

Éléments connus :
- une fenêtre principale plus haute ;
- une ouverture basse en pavés de verre ;
- une rue/sol en pente longitudinale importante.

L'ouverture en pavés de verre doit être positionnée par rapport au niveau local de la rue, pas seulement à `z=0` global.

Le terrain doit être représenté comme terrain extérieur, pas comme un soubassement ou un mur gris collé au bâtiment.

## 8. Côté gauche — structure extérieure

C'est le principal cas géométrique complexe.

Les photos montrent un ensemble rectiligne composé de :
- grande terrasse principalement en bois ;
- partie maçonnée/béton ;
- escalier extérieur béton/maçonnerie ;
- changement de direction ;
- palier de retournement ;
- transition haute vers la terrasse ;
- murets/rampes béton ;
- garde-corps bois sur la terrasse.

La structure conceptuelle la plus récente est :

`sol → première volée béton → palier de retournement → seconde volée → transition béton haute → terrasse bois`

La terrasse doit rester accolée au mur gauche de la maison et se prolonger jusqu'à la zone arrière observée. Elle ne doit pas être recentrée arbitrairement.

## 9. Scene — plateformes

Le contrat Scene a été enrichi pour les plateformes extérieures.

Champs importants :
- `material` ;
- `deck_board_direction` = `x | y | unknown` ;
- `supports` ;
- `edges.x_min` ;
- `edges.x_max` ;
- `edges.y_min` ;
- `edges.y_max` ;
- `access_spans`.

Traitements de bord supportés :
- `none` ;
- `open_railing` ;
- `solid_parapet` ;
- `wall_attached` ;
- `access_opening` ;
- `unknown`.

Règles :
- chaque bord est indépendant ;
- ne jamais supposer la symétrie ;
- un bord collé au bâtiment ne reçoit pas automatiquement de garde-corps ;
- un passage d'escalier peut n'occuper qu'une portion d'un bord via `access_spans` ;
- ne jamais inventer quatre poteaux aux coins d'une terrasse.

## 10. Scene — escaliers

Un escalier tournant doit être décomposé en plusieurs `StairRun` reliés par une ou plusieurs `Platform`.

Une seule `StairRun` ne doit pas changer simultanément x et y.

Les côtés gauche/droit d'une volée sont indépendants :
- `none` ;
- `open_railing` ;
- `solid_parapet` ;
- `unknown`.

Un escalier en béton n'implique pas automatiquement deux murets.

Les connexions escalier→plateforme sont contrôlées avec la largeur réelle de l'escalier et les `access_spans` du bord. L'axe central seul ne suffit plus.

## 11. Relations explicites Survey

Le Survey sait désormais stocker des relations entre objets.

Types mentionnés pendant le développement :
- `connects_to` ;
- `adjacent_to` ;
- `aligned_with` ;
- `supports` ;
- `part_of` ;
- `same_physical_object`.

Seules les relations réellement observées ou confirmées doivent être créées.

Une relation `connects_to` certaine peut devenir une contrainte géométrique lors du passage Survey→Scene.

L'ajout de nouvelles photos au Survey doit conserver les relations déjà validées et seulement les enrichir.

## 12. Connexions géométriques

Des garde-fous ont été ajoutés :
- une plateforme isolée peut être refusée ;
- une extrémité d'escalier flottante peut être refusée ;
- un escalier peut rejoindre le sol, une plateforme ou le bâtiment ;
- une plateforme peut toucher le bâtiment ou un escalier ;
- une relation escalier→plateforme certaine vérifie aussi le passage dans le garde-corps ;
- la largeur complète de la volée doit tenir dans le passage ;
- les connexions plateforme→plateforme certaines sont contrôlées.

Important : ne pas transformer ces contrôles en conventions architecturales universelles. Ils ne doivent contraindre que les relations réellement établies.

## 13. Matériaux extérieurs

Le moteur doit utiliser les champs structurés plutôt que chercher des mots dans les notes.

Matériaux prévus :
- `timber` ;
- `concrete` ;
- `masonry` ;
- `stone` ;
- `metal` ;
- `composite` ;
- `unknown`.

Une compatibilité legacy peut exister pour les anciennes Scenes, mais les nouvelles Scenes doivent renseigner les champs structurés.

## 14. Terrasse bois — rendu LEGO

Le deck bois est maintenant construit avec des pièces LEGO longues orientées selon `deck_board_direction`, plutôt qu'avec une dalle pleine de `BRICK_1X1`.

Le constructeur utilise notamment des longueurs de type :
- 1x8 ;
- 1x6 ;
- 1x4 ;
- 1x3 ;
- 1x2 ;
- 1x1 si nécessaire.

Les garde-corps sont rendus bord par bord.

`wall_attached` ne produit pas de rambarde.

Les `access_spans` conservent de vrais passages dans un garde-corps.

## 15. Terrain

`GradeProfile` possède maintenant `outward_extent`.

Cela permet de représenter une vraie largeur de rue/cour/terrain et non un ruban d'un tenon.

Le terrain LEGO doit être catégorisé `terrain`, séparément des détails de façade.

Pour une ouverture basse, `local_grade_clearance` peut lier le bas de l'ouverture au niveau local interpolé du terrain.

Si une ouverture annonce une garde au sol locale et qu'un profil de terrain correspondant existe, leur cohérence doit être contrôlée.

## 16. Fenêtres et vitrages

Le projet possède un catalogue de vraies fenêtres LEGO validées dans le code.

Le pipeline préfère un assemblage cadre + vitrage réel quand le rectangle de l'ouverture peut être couvert exactement.

Le fallback de menuiserie ne doit plus utiliser des briques de mur pour fabriquer de faux meneaux/traverses internes.

Si une vraie fenêtre LEGO ne peut pas être placée proprement, mieux vaut conserver une ouverture propre que créer une fausse subdivision maçonnée.

Les métadonnées riches des ouvertures doivent être préservées :
- `window_style` ;
- `has_sill` ;
- `has_decorative_surround` ;
- `local_grade_clearance`.

Une régression avait supprimé temporairement certains de ces champs et a été corrigée. Un test de projection existe pour éviter le retour de ce problème.

## 17. Porte-fenêtre et pavés de verre

Le moteur contient une logique Scene-aware pour :
- les portes explicitement vitrées / portes-fenêtres ;
- les ouvertures en pavés de verre.

Ces éléments doivent produire des composants transparents visibles plutôt que de simples trous ou de la maçonnerie.

## 18. Prompt Survey→Scene

Fichier principal :

`frontend/brickhouse-survey-to-scene-prompt.txt`

La version a été renforcée progressivement jusque vers v1.6 pendant la conversation précédente.

Le prompt doit notamment imposer :
- conservation stricte des ouvertures certaines ;
- pas d'invention dans les zones occultées ;
- anti-miroir ;
- segmentation des structures extérieures avant mesure ;
- matériaux structurés ;
- terrasse bois ;
- sens des lames ;
- supports uniquement observés/inférés prudemment ;
- bords indépendants ;
- passages partiels ;
- escalier tournant en plusieurs primitives ;
- cohérence terrain/ouvertures basses ;
- largeur réelle du passage escalier→terrasse ;
- aucun faux meneau/traverse en maçonnerie ;
- audit final du JSON avant rendu.

## 19. Prompt Survey initial et extension

Le Survey initial a aussi été renforcé pour analyser les structures extérieures bloc par bloc et enregistrer les relations visibles.

L'extension de Survey à partir de nouvelles photos doit conserver les relations déjà validées et ne pas repartir de zéro.

## 20. Interface utilisateur future

Objectif : masquer la complexité Survey/Scene/JSON à l'utilisateur normal.

Parcours souhaité :

### Zone photos
Cases guidées, par exemple :
- façade avant ;
- 3/4 avant gauche ;
- côté gauche ;
- arrière / 3/4 arrière ;
- côté droit ;
- 3/4 avant droit.

Chaque photo peut avoir une note utilisateur spécifique.

L'utilisateur peut aussi fournir :
- largeur connue ;
- informations générales ;
- commentaires libres.

### Mode IA externe
BrickHouse doit pouvoir compiler :
- photos ;
- rôles des photos ;
- notes ;
- mesures ;
- instructions IA.

Puis proposer un bouton du type :
`Télécharger le paquet à envoyer à l'IA`

Le logiciel ne doit pas obliger l'utilisateur à choisir ChatGPT/Claude/Gemini. Le parcours doit rester neutre : « une IA ».

L'IA externe doit idéalement renvoyer un seul fichier BrickHouse contenant Survey + Scene ou un format équivalent validable automatiquement.

L'utilisateur réimporte ensuite ce seul fichier.

### Mode API futur
Une zone peut déjà être préparée visuellement pour le futur mode où BrickHouse appellera directement une API IA, sans aller-retour manuel par fichiers.

Les anciens outils techniques doivent rester disponibles dans des options avancées pendant le développement, mais ne doivent pas encombrer le parcours normal.

Le bouton final `Construire ma maquette` doit rester visible dans le parcours normal une fois l'analyse validée.

## 21. Maison test — dernière Scene préparée

Dans la conversation précédente, une Scene locale a été générée :

`brickhouse-architectural-scene-v0.2-consolidated-v5.json`

Elle n'est PAS garantie présente dans GitHub.

Elle contient notamment :
- inventaire principal inchangé : front=6, right=2, left=3, rear=0 ;
- terrasse timber ;
- `deck_board_direction` ;
- supports explicitement inférés ;
- bords indépendants ;
- passages ;
- première volée ;
- palier intermédiaire ;
- seconde volée tournée vers la maison ;
- transition béton haute ;
- terrain droit avec `outward_extent` ;
- ouverture basse droite alignée sur le niveau local de la rue ;
- métadonnées de fenêtres conservées.

Si ce fichier est nécessaire dans une future conversation et n'existe pas dans le dépôt, demander à l'utilisateur de le fournir. Ne pas prétendre l'avoir.

## 22. Dernier état du test visuel utilisateur

Le dernier rendu testé avant les grosses corrections suivantes montrait :
- nombre d'ouvertures correct partout ;
- plus de miroir gauche/droite ;
- façade avant nettement plus cohérente ;
- pente enfin visible ;
- terrasse encore trop générique ;
- escalier encore mal raccordé ;
- un élément extérieur parasite apparaissait sur la façade avant ;
- terrain encore trop proche d'un ruban/soubassement ;
- besoin de meilleures fenêtres LEGO.

Les modifications postérieures à ce rendu ont précisément visé ces défauts.

## 23. Commits récents mentionnés pendant le développement

À vérifier dans GitHub avant de s'y fier :

- `c8abfd16` : contrat Scene / terrasse ;
- `75f518b4` : construction LEGO terrasse directionnelle ;
- `c517472e` : tests terrasse ;
- `ed059055` : prompt IA ;
- `d63481fc` : correction régression champs riches ouvertures ;
- `ea434f3e` : test projection détails d'ouverture ;
- `01cd0663` : raccord escalier/terrasse selon largeur réelle ;
- `5b21b1c6` : tests correspondants ;
- `a6cf7243` : relation ouverture basse / terrain ;
- `48e8f265` : test terrain/ouverture ;
- `776aee71` : suppression des faux meneaux en maçonnerie ;
- `23aa57ea` : terrain / catégorie et surface ;
- `6751c023` : tests/rendu de largeur terrain ;
- `7bb14d37` : raccord plateforme/plateforme ;
- `59402830` : tests de raccord ;
- `748232e5` : prompt Survey→Scene v1.6 ;
- `8cb4be4e` : `outward_extent` dans le contrat ;
- `bb7c8f16` : bords de plateforme explicites ;
- `57d033a2` : passages partiels ;
- `5cdd17d1` : rendu bord par bord ;
- `295a154d` : contrôle d'accès escalier→plateforme ;
- `9cc36109` : matériaux structurés ;
- `1a92169f` : moteur matériaux ;
- `3c0e82ba` : règles génériques plateformes/escaliers ;
- `63f42562` : connectivité externe ;
- `1de0346c` : relations Survey ;
- `eeecaa89` : contrôle relations Survey→Scene.

Ces références servent à retrouver les étapes, mais l'état réel du dépôt prime.

## 24. Méthode de travail attendue dans une nouvelle conversation

1. Lire ce fichier.
2. Inspecter directement le dépôt GitHub.
3. Vérifier l'état réel des fichiers et tests.
4. Ne pas supposer que tous les commits cités sont encore la tête de `main`.
5. Continuer par jalons cohérents.
6. Ajouter/mettre à jour des tests de régression lors des changements de moteur.
7. Mettre à jour les prompts quand le contrat ou le moteur évoluent.
8. Ne pas faire tester l'utilisateur après chaque petite modification.
9. Ne demander un test que lorsqu'un ensemble de changements est réellement testable.
10. Ne guider l'utilisateur avec un bouton de l'interface qu'après avoir vérifié son libellé exact dans le code.

## 25. Priorités immédiates

Avant de déclarer le moteur suffisamment stable pour basculer principalement sur l'interface, vérifier notamment :

- raccord géométrique précis sol→volée→palier→volée→transition→terrasse ;
- séparation visuelle et constructive béton / bois ;
- continuité des passages dans les garde-corps ;
- absence d'éléments extérieurs débordant sur une autre façade ;
- terrain avec vraie surface et pente cohérente ;
- ouverture basse cohérente avec le terrain local ;
- porte-fenêtre toujours présente ;
- fenêtres sans barres de maçonnerie internes ;
- comptes d'ouvertures toujours verrouillés ;
- anti-miroir toujours verrouillé ;
- aucun ajout sur façade arrière si le Survey reste à zéro ouverture.

## 26. Prochaine étape recommandée

Inspecter l'état actuel de `main`, exécuter mentalement/à travers les tests les dernières règles du contrat Scene, puis préparer un nouveau jalon global de test avec la Scene consolidée la plus récente.

Si la Scene v5 n'est pas disponible dans le dépôt ou les fichiers de la nouvelle conversation, demander à l'utilisateur de la fournir uniquement au moment où elle devient réellement nécessaire.

Après un test global satisfaisant du moteur, accélérer la simplification de l'interface utilisateur décrite plus haut.
