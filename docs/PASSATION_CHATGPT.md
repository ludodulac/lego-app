# PASSATION CHATGPT — Boldungo / BrickHouse

Dernière mise à jour : 2026-08-27
Dépôt : `ludodulac/lego-app`

## Instruction impérative à la prochaine conversation

Commence par lire **ce fichier en entier**, puis inspecte l’état réel de `main`, des issues, PR et CI avant toute modification. Ne suppose jamais que les numéros/états CI ci-dessous sont encore actuels.

Le travail doit continuer de façon autonome autant que possible. Ne redemander l’utilisateur que lorsqu’une information ou action humaine est réellement nécessaire.

## But produit — ne pas perdre ce cap

Boldungo / BrickHouse doit transformer plusieurs photos d’une maison réelle en :

`photos -> compréhension architecturale cumulative -> scène 3D prudente -> modèle LEGO précis et constructible -> BOM/liste de pièces -> ordre de montage -> notice de montage`

Le but n’est PAS seulement de produire un joli aperçu 3D. Le visualiseur architectural sert à vérifier la compréhension avant conversion. Le résultat final attendu est une vraie maquette LEGO ressemblante, construite avec des pièces précises et une notice, d’abord avec des briques simples/robustes puis progressivement avec des détails plus fins (gouttières, bordures, appuis, encadrements, garde-corps, menuiseries, etc.) quand les pièces/techniques sont validées.

Règle centrale : **ne jamais inventer une géométrie simplement pour obtenir un rendu complet**. Une inconnue doit rester inconnue. Une partie suffisamment connue peut cependant être construite sans attendre que toute la maison soit résolue.

## Les cinq photos de référence

La conversation utilisateur contient cinq photos réelles de la même maison. Elles sont la référence visuelle du cas BrickHouse. Les fixtures principales du dépôt sont :
- `tests/fixtures/brickhouse_survey_current.json`
- `tests/fixtures/brickhouse_scene_current.json`
- rechercher également `independent` / `brickhouse` dans fixtures/tests pour les analyses indépendantes.

La prochaine conversation doit continuer à raisonner à partir de ces cinq vues et des données structurées déjà capturées. Si les images elles-mêmes ne sont pas disponibles dans une nouvelle conversation, ne prétends pas les voir : utilise les observations indexées ici/fixtures et demande seulement une nouvelle fourniture des photos lorsqu’un contrôle visuel direct devient réellement nécessaire.

## Méthode d’analyse photo voulue par l’utilisateur — TRÈS IMPORTANT

L’utilisateur a décrit explicitement comment il raisonne lui-même « comme si j’étais l’IA ». Cette méthode doit devenir le cœur de l’analyse amont, pas seulement un prompt ponctuel.

### Boucle de raisonnement

Pour chaque photo :
1. **Observer exhaustivement avant de mesurer** : objets, ouvertures, matériaux, couleurs architecturales, relations, limites du bâtiment, terrain, détails, occultations.
2. Séparer strictement :
   - fait directement visible ;
   - identification probable d’un objet ;
   - déduction géométrique ;
   - estimation par référence ;
   - hypothèse ;
   - inconnu/question ouverte.
3. Poser des questions internes : « qu’est-ce que cela pourrait être ? », « qu’est-ce que cet indice implique ou n’implique pas ? », « quelle autre vue permettrait de le vérifier ? ».
4. Convertir seulement ce qui est défendable en **primitives spatiales provisoires** : volume/boîte, plan, ouverture, pente, escalier, terrasse, etc. Une primitive peut avoir position/relation connue mais dimensions inconnues.
5. Analyser la photo suivante dans **le même espace 3D partagé**, reconnaître les mêmes objets entre vues, confirmer/réfuter/raffiner les hypothèses précédentes plutôt que repartir de zéro.
6. Conserver l’historique et la provenance : une nouvelle photo affine une hypothèse ; elle ne doit pas effacer silencieusement le raisonnement précédent.
7. Construire un graphe de contraintes et résoudre progressivement les « énigmes » par convergence de plusieurs indices faibles.
8. Demander une photo/mesure à l’utilisateur seulement si son **gain d’information attendu** est suffisamment important pour la reconstruction LEGO.

### Hiérarchie des connaissances / mesures

Ne jamais confondre une valeur typique avec une mesure réelle. Conserver une hiérarchie du type :

`mesuré/visible -> déduit géométriquement -> estimé depuis référence reconnue -> valeur typique externe -> hypothèse`

Une connaissance générale peut donner une plage/probabilité, jamais automatiquement une mesure du bâtiment. Exemple : largeur typique d’un trottoir, hauteur d’un garde-corps, dimensions connues d’un type de poteau, module d’une brique de verre, dimensions usuelles d’une fenêtre. Plusieurs contraintes indépendantes peuvent ensuite resserrer fortement l’intervalle.

L’IA peut et doit exploiter davantage de connaissances que l’humain quand cela aide : reconnaître précisément un objet standard, rechercher/connaître ses dimensions typiques, exploiter perspective/lignes de fuite, répétitions, proportions et objets de référence. Mais la provenance et l’incertitude doivent rester explicites.

Exemple de sortie conceptuelle souhaitée : « pente estimée 6–9°, confiance moyenne, trois indices indépendants concordent ; telle nouvelle vue ferait passer la confiance à élevée ». La précision demandée doit aussi dépendre de ce qui est nécessaire pour choisir les briques LEGO.

### Distinctions importantes apprises des descriptions humaines

Un objet peut être :
- observé sans être identifié (« petite boîte ou lampe ») ;
- identifié sans être localisé précisément ;
- localisé relativement sans dimensions ;
- estimé avec incertitude ;
- structurel ou temporaire ;
- pertinent ou non pour la maquette LEGO.

Ne pas supprimer un objet réel juste parce qu’il est peu important ; le classer comme non prioritaire/temporaire et permettre éventuellement à l’utilisateur de choisir de l’omettre (fils, travaux inachevés, pots, objets posés, etc.).

## Notes humaines indexées sur les photos — conserver ces indices

Ces notes viennent directement des descriptions spontanées de l’utilisateur et doivent servir de cas de référence pour la logique de raisonnement, pas de mesures certaines.

### Façade avant / photo 1 décrite

- Maison blanche, façade perçue comme plutôt carrée mais non mesurée.
- Deux fenêtres au niveau supérieur, deux au niveau intermédiaire.
- Rez-de-chaussée : à droite une porte-fenêtre, partiellement occultée par une plante ; petite fenêtre basse alignée verticalement avec celles au-dessus.
- Porte-fenêtre : deux vantaux s’ouvrant au milieu ; quatre vitrages visibles, deux vitrages supérieurs rectangulaires et deux inférieurs plus carrés.
- Fenêtres décrites comme deux grands vitrages rectangulaires par fenêtre ; menuiseries/volets blancs dans certaines vues ; volets pliants/repliables observés sur certaines fenêtres.
- Encadrements/bordures autour des fenêtres, aspect pierre/enduit rapporté, légèrement plus foncé que la façade. La salissure de façade ne doit pas être traitée comme architecture.
- Partie basse de façade légèrement rosée/beige, limite approximativement au bas de la petite fenêtre.
- À gauche : début d’un portail gris ; jardinière/caisson bois au sol.
- Trace/vestige visible d’un ancien mur au-dessus/près d’une fenêtre : à conserver comme observation, sans inventer sa géométrie.
- Toiture zinc visible, pente assez faible mais angle à résoudre ; environ sept extrémités de poutrelles/chevrons visibles en haut selon le comptage humain (à vérifier, pas valeur certaine).
- Cheminée proche du bord gauche avec deux sorties cylindriques en brique/terre cuite ; antenne derrière. Une autre cheminée à droite paraît probablement appartenir à l’immeuble voisin : ownership à résoudre par recoupement.
- Parterre de cailloux devant la maison.
- Rue côté droit semblant monter : hypothèse à confirmer par vue latérale.

### Façade droite / vue latérale décrite

- La rue/trottoir longe le mur et monte probablement. Indice important : la bande de peinture/soubassement horizontale visible sur la façade avant se raccorde puis disparaît progressivement dans le niveau du trottoir. Utiliser ce type d’indice pour estimer la pente, avec perspective et distance, sans fabriquer un angle certain.
- Petit trottoir estimé humainement autour de 50 cm : **estimation seulement**. L’IA peut utiliser des distributions de dimensions typiques + autres indices pour raffiner.
- Végétation sur le trottoir/bande latérale, possiblement cultivée ou spontanée : non structurel.
- Ouverture basse côté droit ; une ouverture est décrite comme faite de briques de verre, comptage humain possible ~6 x 6 mais à vérifier. Le logiciel pourrait demander un comptage exact si cela change la maquette.
- Mur perçu comme épais grâce aux embrasures.
- Limite de la maison repérée près d’un poteau électrique type treillis/échelle ; au-delà se trouve l’autre immeuble. Ce poteau est aussi un exemple d’objet standard potentiellement utilisable comme référence métrique si son type est identifié avec confiance.
- La cheminée plus lointaine paraît appartenir à l’autre immeuble après cette vue.
- Gouttière en haut ; descente de gouttière sur un bord, aspect zinc.
- Tuyau/câble électrique, tuyaux de travaux inachevés, coffret bas (eau/électricité non identifié), petite ouverture basse dans le trottoir/mur. À identifier/localiser mais potentiellement omettre du LEGO selon pertinence.
- Fenêtre haute avec volets blancs pliants et fenêtre blanche ouvrant vers l’intérieur, grand vitrage vertical selon l’observation humaine.

### Façade gauche / terrasse décrite

- Fenêtre au niveau supérieur, clairement en retrait ; embrasure/mur perçu épais. L’estimation humaine d’environ 20 cm ne doit PAS devenir une mesure certaine.
- Au niveau terrasse : porte-fenêtre à droite, fortement en retrait ; porte d’entrée sous la fenêtre supérieure, partiellement cachée par le garde-corps et semblant ouverte sur une vue.
- Terrasse en bois : plancher bois, garde-corps avec nombreux barreaux/planches verticales et lisse horizontale ; terrasse légèrement oblique/évasée plutôt qu’un rectangle parfaitement orthogonal, à confirmer contre perspective.
- Sous terrasse : poteau bois de charpente/menuiserie, pots/bac/compost possibles, objets secondaires.
- Un mur blanc prolonge une partie de la terrasse.
- Escalier extérieur descend et dépasse du volume de la maison ; la perspective suggère un escalier en deux volées / changement de direction possible, mais la partie cachée reste à confirmer. L’utilisateur a explicitement proposé de demander une photo prise depuis la terrasse si cette inconnue devient bloquante.
- Gouttière descendante raccordée à la toiture.
- La cheminée/antenne proche vue depuis la façade avant est cohérente depuis cette vue et son emplacement peut être triangulé.
- Petite lampe ou petite boîte sous une fenêtre : objet observé mais identification incertaine.

### Première description humaine précédente de la zone terrasse

- Maison blanche ; fenêtre supérieure divisée/ouvrante au milieu et légèrement enfoncée.
- Sous cette fenêtre, ouverture sombre probablement porte d’entrée ; à droite ouverture plus large probablement porte-fenêtre car elle descend vers le sol et s’ouvre au milieu.
- Barrière bois posée sur plancher/structure bois ; poteau bois sous terrasse.
- Terrasse semble continuer avec un mur béton/blanc vers la porte d’entrée ; présence/absence d’une marche inconnue.
- Escalier perpendiculaire à la maison et dépassant vers l’extérieur ; créer mentalement un volume englobant mais ne pas inventer la suite cachée.
- Gouttière au sommet du mur ; plusieurs cheminées visibles mais ownership à résoudre.
- Bord droit de terrasse décrit comme légèrement oblique et rejoignant le mur ; raccord possible avec le morceau de terrasse vu sur une autre photo.

Ces notes doivent être considérées comme **observations/hypothèses humaines de référence**, à recouper avec les fixtures et les photos, jamais comme vérité métrique automatique.

## Travail déjà réalisé depuis l’ancienne passation

Depuis la version précédente de ce fichier, beaucoup de petites PR ont été fusionnées. Inspecter l’historique réel pour les détails. Les acquis importants à préserver sont :

- le visualiseur ne transforme plus une pente de toit `null` en `0°` ;
- terrain observé mais non métré reste signalé sans surface inclinée arbitraire ;
- terrasse, supports, renforts, garde-corps, escalier et parapets ont été enrichis de façon prudente ;
- la chaîne directe `ArchitecturalScene -> LEGO -> BOM -> AssemblyPlan` existe ;
- une scène incomplète peut produire les **premières briques fiables** sans forcer les zones inconnues ;
- le viewer peut progresser selon l’ordre d’assemblage et des travaux ont été faits sur les étapes/caméras de notice ;
- la discrétisation métrique -> grille LEGO mesure maintenant ses erreurs et l’échelle peut être optimisée sans modifier une échelle explicitement demandée ;
- les cheminées suffisamment résolues peuvent survivre jusqu’au BrickModel/BOM/assemblage ;
- BH-083 a ajouté une représentation de l’épaisseur/retrait des murs fondée sur les preuves, puis de vraies couches de maçonnerie/retraits de vitrage quand les valeurs sont suffisamment fiables, y compris builds partiels et multi-volumes ;
- un retrait observé mais non métriquement résolu est exposé comme problème de fidélité plutôt que transformé en centimètres inventés ;
- PR #228 a ajouté aux détails de fenêtres une sémantique par ouverture : `sill`, `left_jamb`, `right_jamb`, `head`, `surround_base` afin de pouvoir ensuite choisir de meilleures pièces LEGO sans changer l’évidence architecturale.

## État exact au moment de cette passation

- PR #228 `Track architectural window trim as explicit LEGO detail roles` : CI vérifiée verte puis fusionnée dans `main` (squash, merge commit `312edec6cdf881b8268010efc5caeef5440f5adb`).
- Issue #222 / BH-083 : fermée comme terminée après #228.
- Nouvelle issue #229 / **BH-084 — Refine openings with faithful LEGO trim, shutters and door assemblies** : ouverte. C’est le prochain grand chantier.
- Sous-issue #230 / **BH-084A — Compact semantic window trim into longer canonical LEGO bricks** : ouverte. C’est la prochaine petite tranche recommandée.
- Aucune PR BH-084A n’avait encore été créée au moment de cette mise à jour.

Toujours vérifier l’état réel avant d’agir.

## Prochaine trajectoire recommandée

### Immédiat : BH-084A (#230)

Utiliser les rôles sémantiques de #228 pour remplacer les suites anonymes de `BRICK_1X1` par les briques canoniques les plus longues compatibles (`1x2`, `1x3`, `1x4`, `1x6`, `1x8`, etc.) **sans changer une seule cellule architecturale occupée** et sans combler les ouvertures. Ajouter tests d’équivalence de cellules et réduction du nombre de pièces. Garder provenance `opening_id` / `trim_role` autant que possible.

Le catalogue M0 actuel contient surtout des briques standard 1xN/2xN. `piece_capabilities.py` impose qu’une pièce soit explicitement `PLACEMENT_APPROVED` avant placement automatique. Respecter ce garde-fou : présence dans un dataset LEGO != autorisation de placement.

### Ensuite dans BH-084 (#229)

1. Raffiner appuis/encadrements avec pièces simples validées.
2. Représenter les volets pliants uniquement sur ouvertures où ils sont observés.
3. Améliorer la porte-fenêtre / French door (deux vantaux, composition vitrée observée) sans inventer sur les vues occultées.
4. Maintenir les menuiseries sur le plan de retrait BH-083.
5. Faire apparaître les inconnues de composition comme questions, pas comme choix silencieux.
6. Synchroniser BrickModel, BOM, AssemblyPlan, viewer et tests.
7. Seulement ensuite promouvoir des pièces plus subtiles du catalogue après validation de géométrie/orientation/connexion.

### Cap produit après les ouvertures

Continuer à rapprocher visiblement les premières briques de la maison : toiture zinc/pente quand résolue, gouttières, terrasse/escaliers constructibles, détails de façade pertinents, puis renforcer la **notice** (étapes lisibles, ordre stable, caméra, pièces ajoutées par étape). Ne pas rester indéfiniment dans l’analyse : l’analyse doit alimenter le logiciel et la construction LEGO.

## Méthode de travail souhaitée

Petites PR isolées :
1. défaut précis ;
2. correction sans hypothèse non prouvée ;
3. test de régression ;
4. vérifier CI ;
5. fusionner seulement si vert ;
6. passer au défaut suivant.

Ne pas modifier le workflow CI sans preuve d’un problème de workflow. Les automatisations GitHub peuvent parfois avoir des comportements de déclenchement particuliers.

## Préférences utilisateur

- Continuer de façon autonome autant que possible ; ne demander la main que lorsque nécessaire.
- L’utilisateur est impatient de **voir les premières briques se monter avec précision**, puis de passer à la notice : privilégier les travaux qui rapprochent directement de ce résultat.
- Les raffinements visuels architecturaux sont utiles s’ils empêchent une mauvaise reconstruction, mais ne doivent pas devenir une fin en soi.
- Lorsqu’un nouveau terme technique est introduit, fournir un petit glossaire/explication, sans répéter indéfiniment les termes déjà expliqués.

## Première action de la prochaine conversation

1. Lire ce fichier en entier.
2. Inspecter `main`, issues #229/#230, PR ouvertes et CI.
3. Lire au minimum `backend/brickhouse/bricks/facade_details.py`, `catalog.py`, `piece_capabilities.py`, les tests associés et le chemin qui convertit `FacadeDetailPlacement` en `BrickModel`.
4. Implémenter BH-084A (#230) par petite PR avec tests, attendre CI verte, fusionner.
5. Continuer BH-084 sans solliciter l’utilisateur tant qu’aucune information visuelle réellement bloquante n’est requise.
