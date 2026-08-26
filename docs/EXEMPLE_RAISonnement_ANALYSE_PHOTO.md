# Exemple utilisateur — raisonnement d’analyse photo

Ce document conserve un exemple concret de la manière dont l’utilisateur souhaite que l’IA raisonne à partir d’une seule image avant fusion multi-vues. Il ne constitue pas une vérité géométrique sur BrickHouse : il sert de **trace de référence de méthode** pour les prompts, les contrats de raisonnement et les tests futurs.

## Principe

L’analyse doit avancer par couches :

1. **Décrire ce qui est directement visible** sans reconstruire trop tôt.
2. **Qualifier chaque élément** (fenêtre, porte possible, terrasse, poteau, escalier, gouttière, cheminée, voisin, etc.) avec un niveau de certitude distinct de son existence.
3. **Formuler les questions et hypothèses intermédiaires** déclenchées par l’image.
4. **Proposer des primitives spatiales simples** (volume, plan, ouverture, boîte englobante, axe, relation d’adjacence) uniquement lorsque l’image les justifie.
5. **Conserver explicitement ce qui reste inconnu** et identifier quelle vue supplémentaire pourrait le résoudre.
6. **Recouper ensuite avec les autres photos**, reconnaître les mêmes objets et raffiner progressivement la géométrie.

## Exemple fourni par l’utilisateur

> Sur cette image je vois une Maison Blanche avec une fenêtre en haut cette fenêtre elle est séparée en deux parce qu'il y a une ouverture au milieu la fenêtre est légèrement enfoncée à l'intérieur de la maison à partir de là je peux imaginer déjà la forme prendra cet espace sous cette fenêtre je vois qu'il y a une ouverture c'est un peu sombre mais ça doit être la porte d'entrée à droite je vois une autre ouverture un peu plus large qui est aussi une porte mais ça m'a l'air d'être comme une fenêtre qui s'ouvre au milieu donc c'est sûrement une porte-fenêtre parce qu'elle m'a l'air plus longue et a l'air de descendre jusqu'en bas même si on ne voit pas très bien je vois qu'il y a une barrière en bois posé sur un plancher en bois en tout cas un sol qui est formé de poutre en bois avec la même couleur exactement que le poteau qui est en dessous qui a une forme de menuiserie, en tout cas d'architecture en bois pour maison donc c'est un poteau en bois. Cette terrasse en bois continue avec un mur en béton blanc qui descend jusqu'en bas et ça m'a l'air d'être en face de la porte d'entrée donc il doit y avoir une continuité de terrasse à cet endroit là alors je ne vois pas s'il y a une marche pour l'instant je ne peux pas le définir et je vois un escalier qui descend mais c'est escalier qui descend si je calcule bien je vois que il est perpendiculaire à la maison et donc il dépasse un peu de la Maison Blanche vers l'arrière. Cela me permet de définir un autre espace cubique dans lequel je pourrais insérer cet escalier je ne vois pas la suite de l'escalier donc ça je ne peux pas le voir pour l'instant il me faudra une autre photo en haut de ce mur blanc je vois qu'il y a une gouttière et des cheminées à gauche la cheminée appartient peut-être à cette maison par contre derrière je vois une autre cheminée qui appartient sûrement à l'immeuble Eric et derrière à droite je vois qu'il y a une cheminée et une antenne je reconnais que la terrasse en bois du côté droit par dans un angle qui n'est pas tout à fait droit qui est un peu oblique et qui vient toucher le bord du mur donc la terrasse est attenante au mur je peux déjà aussi former une forme dans l'espace à partir de ça et je me souviens que j'ai vu une photo de la façade où je voyais ce bout de terrasse donc je peux faire le raccordement maintenant et je ferai pareil avec la photo suivante on verra mieux l'escalier.

## Décomposition machine souhaitée

Le même raisonnement peut être rendu exploitable par le logiciel sans transformer les hypothèses en faits.

### Observations directes

- bâtiment principal enduit/blanc visible ;
- une ouverture haute vitrée, divisée en deux et légèrement en retrait du plan de façade ;
- deux ouvertures plus basses visibles mais partiellement sombres/ambiguës ;
- garde-corps et platelage en bois ;
- au moins un poteau en bois de même famille visuelle que la terrasse ;
- volume/mur blanc massif adjacent à la terrasse ;
- volée d’escalier visible ;
- gouttière visible au-dessus du mur ;
- plusieurs cheminées et une antenne dans la scène ;
- bord de terrasse non orthogonal/oblique visible et en contact avec un mur.

### Hypothèses à conserver séparément

- l’ouverture basse sombre **pourrait** être la porte d’entrée ;
- l’ouverture basse plus large **pourrait** être une porte-fenêtre ;
- le mur/volume blanc **pourrait** supporter ou prolonger une surface de circulation en face de l’entrée ;
- l’escalier semble approximativement perpendiculaire au bâtiment et dépasser vers l’arrière ;
- une cheminée de gauche **pourrait** appartenir au bâtiment cible ;
- d’autres cheminées appartiennent probablement à des bâtiments voisins ;
- le morceau de terrasse visible pourrait être le même objet que celui aperçu dans une autre vue.

Aucune de ces hypothèses ne doit devenir automatiquement une propriété métrique de `ArchitecturalScene`.

### Questions ouvertes

- l’ouverture basse sombre est-elle réellement une porte ?
- l’ouverture large est-elle une porte-fenêtre, une grande fenêtre ou un autre type d’ouverture ?
- existe-t-il une marche ou une rupture de niveau entre le volume blanc et la terrasse ?
- où continue exactement l’escalier dans la zone occultée ?
- quelle cheminée appartient au bâtiment cible ?
- l’angle oblique de la terrasse est-il réel en plan ou principalement dû à la perspective ?
- le tronçon de terrasse visible correspond-il bien au même objet que sur la photo de façade ?

### Primitives spatiales provisoires autorisées

Lorsque la visibilité le permet, l’IA peut créer des représentations **qualitatives et non métriques** :

- un plan de façade et des ouvertures avec ordre relatif ;
- une boîte/volume pour la terrasse visible ;
- une boîte ou un corridor spatial englobant pour la volée d’escalier visible ;
- un volume massif distinct pour le mur/ouvrage blanc ;
- une relation `connects_to` ou `adjacent_to` seulement lorsque le contact est réellement visible ;
- une association multi-vues candidate pour le même objet physique.

Ces primitives doivent rester révisables. Une nouvelle vue peut préciser leur forme, invalider une hypothèse ou scinder un objet provisoire en plusieurs primitives.

## Règle de conception à retenir

La valeur de l’IA ne vient pas d’un saut direct « pixels → modèle 3D ». Elle vient d’une boucle explicable : **voir → décrire → questionner → proposer prudemment → recouper → raffiner → seulement ensuite mesurer/construire**. Les inconnues utiles doivent survivre dans l’état de raisonnement afin que la vue suivante puisse les résoudre au lieu de recommencer l’analyse de zéro.
