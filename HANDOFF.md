# BrickHouse — Passation persistante

Dernière mise à jour : 2026-08-23

## À LIRE EN PREMIER

Ce fichier est la passation de développement de BrickHouse. Dans une nouvelle conversation :
1. lire ce fichier ;
2. inspecter directement `main` dans `ludodulac/lego-app` avant toute modification ;
3. considérer GitHub comme source de vérité si ce document et le code divergent ;
4. travailler directement dans GitHub quand les outils le permettent ;
5. avancer par jalons cohérents et ne demander un test utilisateur que lorsqu'il apporte réellement de l'information.

## 1. Objectif produit

BrickHouse transforme plusieurs photos d'un bâtiment réel en reconstruction architecturale cohérente, puis en maquette LEGO.

Le pipeline conceptuel est :

`photos multi-vues → topologie/correspondances → ArchitecturalSurvey → ArchitecturalScene → contrôles géométriques → approximation LEGO → viewer / nomenclature / instructions`

L'IA ne doit jamais raisonner naïvement photo par photo. Elle doit reconnaître les mêmes objets entre les vues : ouvertures, angles, toiture, terrain, terrasse, escaliers, volumes secondaires, occultations, éléments répétitifs, etc.

Hiérarchie de vérité à respecter :
1. topologie et correspondances multi-vues ;
2. nombre exact d'ouvertures par pan ;
3. identité/type des ouvertures ;
4. ordre et alignements ;
5. position ;
6. dimensions/proportions ;
7. structures extérieures ;
8. terrain ;
9. détails architecturaux ;
10. traduction LEGO.

Une couche basse ne doit jamais modifier un fait certain d'une couche haute pour faciliter la construction LEGO.

## 2. Règles universelles

- Le projet doit fonctionner pour n'importe quel bâtiment. La maison actuelle est seulement un benchmark.
- Ne jamais coder une règle spécialement pour la maison test.
- Ne jamais compléter automatiquement une zone occultée.
- Une géométrie plausible ne doit pas devenir certaine simplement parce qu'elle permet de fermer proprement une circulation.
- Une porte en hauteur peut réellement donner dans le vide : ne pas inventer balcon, palier, terrasse ou escalier.
- Ne jamais inventer une ouverture cachée.
- Ne jamais inverser gauche/droite.
- Repère canonique : x = gauche→droite vu de face, y = avant→arrière, z = bas→haut.
- Nettoyer conceptuellement salissures/vieillissement est acceptable ; supprimer un vrai encadrement, changement de matériau ou détail architectural ne l'est pas.
- Si le schéma ou le moteur LEGO ne sait pas représenter une géométrie réelle, conserver la vérité architecturale et déclarer la perte de fidélité au lieu de la transformer silencieusement.

## 3. Architectures atypiques / trajectoire long terme

BrickHouse ne doit pas rester enfermé dans « quatre murs rectangulaires + toit ».

Une couche géométrique générique a commencé à être introduite pour permettre progressivement :
- bâtiments orthogonaux ;
- façades polygonales/inclinées ;
- surfaces libres/maillages ;
- à terme enveloppes courbes et sous-assemblages LEGO complexes.

Voir notamment `backend/brickhouse/geometry/surfaces.py` et `docs/architecture-freeform-surfaces.md` si toujours présents sur `main`.

Une seule photo peut établir silhouette/topologie visible mais ne justifie pas l'invention de la profondeur cachée.

## 4. Stratégie photo actuelle

Le produit doit être puissant avec quelques bonnes photos, sans prétendre qu'un nombre fixe suffit à tous les bâtiments.

Principe actuel : **quelques vues générales à fort recouvrement + vues supplémentaires ciblées si elles apportent un vrai gain d'information**.

L'interface a été étendue vers :
- 6 zones de vues de base guidées ;
- plusieurs photos possibles dans une même zone lorsqu'elles représentent le même côté/angle sous des positions différentes ;
- jusqu'à 6 vues supplémentaires ciblées ;
- maximum total 12 photos.

Les libellés des zones sont des repères utilisateur, pas une vérité architecturale. Le handoff externe indique explicitement qu'un libellé ne doit jamais forcer une interprétation contraire à l'image. Les vues supplémentaires et les vues multiples d'une même zone doivent raffiner les mêmes objets, pas créer artificiellement de nouveaux objets.

Le benchmark principal actuel doit rester les **5 photos originales**. Des photos supplémentaires de la maison ont été fournies ensuite et servent de vérité de contrôle : elles ne doivent pas être utilisées pour rendre artificiellement le benchmark 5 photos parfait. Elles servent à déterminer ce qui était déductible, ce qui devait rester incertain et ce qui aurait justifié une demande de vue ciblée.

## 5. Maison benchmark — faits verrouillés

Cette section décrit le cas de validation, pas des règles génériques.

Repères historiques des 5 vues :
- photo 1 = façade avant ;
- photo 2 = côté droit ;
- photo 3 = côté gauche ;
- photo 4 = côté gauche rapproché ;
- photo 5 = principalement arrière, avec encore du côté gauche autour du coin.

Inventaire d'ouvertures du corps principal :
- avant : 6 ;
- droite : 2 ;
- gauche : 3 ;
- arrière : 0.

L'arrière ne doit recevoir aucune fenêtre inventée.

Côté gauche : ensemble complexe terrasse/escalier. Le modèle conceptuel utilisé lors des Scenes manuelles était :

`sol → première volée béton → palier de retournement → seconde volée → transition béton haute → terrasse bois`

Attention : les dernières réflexions ont précisément conclu qu'une chaîne cachée ne doit PAS être fabriquée seulement pour obtenir cette continuité. Chaque primitive et chaque connexion doit être soutenue par le Survey ou rester incertaine.

La terrasse est principalement bois, avec parties béton/maçonnerie, garde-corps bois et structures de support. La rue du côté droit est en pente et l'ouverture basse en pavés de verre doit être reliée au niveau local du terrain.

## 6. Scene / structures extérieures

Les `Platform` supportent notamment :
- `material` ;
- `deck_board_direction = x | y | unknown` ;
- `supports` ;
- `edges.x_min/x_max/y_min/y_max` ;
- `access_spans` ;
- rattachement de volume (`host_volume_id`) dans les évolutions récentes.

Traitements de bord :
- `none` ;
- `open_railing` ;
- `solid_parapet` ;
- `wall_attached` ;
- `access_opening` ;
- `unknown`.

Un bord collé au bâtiment ne reçoit pas automatiquement de garde-corps. Ne jamais inventer quatre poteaux aux coins d'une terrasse.

Un escalier tournant est segmenté en plusieurs `StairRun` reliées par des `Platform`. Une `StairRun` ne doit pas changer x et y simultanément. `left_edge`/`right_edge` suivent le sens start→end. Les coordonnées start/end représentent l'axe central de la volée et sa largeur est centrée autour de cet axe.

Les raccords escalier→plateforme contrôlent la largeur réelle de la volée et le passage réel (`access_span`). Les plateformes sont quantifiées vers l'extérieur lorsqu'il faut préserver leur emprise.

Les primitives extérieures de Scene doivent réutiliser les IDs stables des observations Survey correspondantes. Ne pas créer un palier ou une volée absente du Survey pour fermer une circulation.

## 7. Terrain

`GradeProfile.outward_extent` permet une vraie surface de rue/cour/terrain.

Le terrain est catégorisé `terrain`, séparément des détails de façade.

Le moteur prend en compte les altitudes négatives/descendantes dans l'origine verticale globale au lieu d'écraser le terrain à z=0.

`local_grade_clearance` permet de contrôler une ouverture basse relativement au niveau local interpolé du terrain.

Une pente Scene ne doit pas être créée sans observation Survey correspondante.

## 8. Ouvertures

Les métadonnées riches doivent survivre à toute la projection :
- `window_style` ;
- `has_sill` ;
- `has_decorative_surround` ;
- `local_grade_clearance` ;
- rangs qualitatifs horizontaux/verticaux lorsqu'ils sont disponibles.

Les comptes, IDs, façades, positions et dimensions des ouvertures sont protégés par des tests de régression.

Le moteur ne doit jamais fabriquer de meneaux/traverses en briques de mur dans une fenêtre.

Règles actuelles :
- vraie fenêtre LEGO cadre + vitrage si géométriquement adaptée ;
- une grande fenêtre `simple` ne doit pas être subdivisée uniquement pour réussir le remplissage ;
- styles `paired` / `four_pane` peuvent autoriser des subdivisions parce que le style les justifie ;
- sinon ouverture propre ou remplissage transparent sans faux montants opaques ;
- encadrement architectural rendu autour de l'ouverture, jamais dans le vitrage ;
- pavés de verre et portes vitrées ont une logique Scene-aware ;
- les négations textuelles du type « non vitrée » doivent être traitées avant les mots positifs.

## 9. Toitures

`ArchitecturalScene` accepte davantage de types que l'ancien moteur M0 : `flat`, `gable`, `hip`, `shed`, `mansard`, `gambrel`, `butterfly`, `other` (vérifier le code actuel).

Le moteur LEGO ne doit pas transformer silencieusement un type non supporté en faux toit à deux pans. Les limitations finales sont reportées dans `fidelity_issues`.

Le catalogue de pentes exploitées a été élargi au-delà de 33°/45°, notamment avec une famille 18° validée. Vérifier l'état réel sur `main`.

La logique de pignon est générique : un pignon avant/arrière et un pignon gauche/droite n'ont pas la même orientation de faîtage. Un bug d'orientation des briques longues pour les pignons gauche/droite a été corrigé.

## 10. Catalogue LEGO / capacités

Le dépôt contient un catalogue riche (`data/processed/piece_types_master.csv`) avec beaucoup plus de familles que le moteur historique M0 : plates, tiles, slopes de plusieurs angles, fenêtres, portes, etc.

Présence dans le catalogue ≠ autorisation automatique de placement.

Une couche de capacités a été ajoutée avec plusieurs niveaux, jusqu'à `PLACEMENT_APPROVED` / techniques spéciales. Le pipeline vérifie que les pièces réellement générées sont autorisées pour le placement déterministe.

Objectif long terme : slopes, wedges, curved slopes, hinges, SNOT et sous-assemblages pour approximer les architectures complexes, mais uniquement quand leur géométrie/connectivité est réellement modélisée.

## 11. Fidélité finale

L'export possède un contrat `fidelity_issues` pour distinguer :
- ce qui existe architecturalement mais n'est pas encore rendu correctement en LEGO ;
- ce qui est réellement absent.

Une perte intermédiaire restaurée ensuite par le pipeline Scene-aware ne doit pas être signalée comme perte finale.

Le viewer possède une section « Fidélité architecturale » pour exposer les approximations/limitations finales.

Les structures extérieures faiblement confiantes peuvent également générer un `fidelity_issue` plutôt que d'être présentées comme des faits aussi sûrs que les ouvertures verrouillées.

## 12. Matériaux / viewer / instructions

Les matériaux `timber`, `concrete`, `masonry`, `stone`, `metal`, `composite` sont conservés plus loin dans le pipeline afin que bois, béton, maçonnerie et terrain ne soient pas tous rendus comme le même matériau.

Le plan de montage distingue maintenant des phases comme :
- Terrain ;
- Structure ;
- Structures extérieures ;
- Fenêtres ;
- Façades ;
- Toiture.

Le viewer propose des vues canoniques Avant / Arrière / Gauche / Droite et Perspective. Le miroir gauche/droite a été corrigé et doit rester protégé.

## 13. Prompts IA — état conceptuel récent

Toujours vérifier les versions réelles dans `frontend/`.

Les évolutions récentes incluent :
- prompt topologique autour de v0.5 : qualité/gain d'information avant quantité, possibilité de demander une vue ciblée ;
- Survey autour de v1.9 : densité de couverture, relations, IDs stables, rangs qualitatifs des ouvertures, prudence sur les zones occultées ;
- extension Survey append-only : nouvelles vues raffinent les observations existantes et conservent l'historique ;
- Survey→Scene autour de v2.5 : portée générique, architectures non orthogonales, volumes, IDs Survey→Scene, coordonnées extérieures explicites, incertitude, interdiction de créer une primitive extérieure absente du Survey.

Ne jamais remplacer ces règles par des faits propres à la maison benchmark.

## 14. Multi-volumes

La Scene peut contenir plusieurs volumes. Les informations de visibilité/occlusion et plateformes ont été étendues pour pouvoir être rattachées au bon volume (`volume_id`, `host_volume_id` selon le contrat actuel).

Les validations ne doivent pas supposer que tout appartient au volume principal.

## 15. Dernier test visuel significatif

Un rendu global a été obtenu après les grosses corrections. Résultat utilisateur : « ça commence à ressembler à quelque chose », mais terrasse et escalier restaient mal respectés.

Les nouvelles photos supplémentaires ont ensuite montré plus clairement la vraie structure extérieure. Décision produit :
- conserver les 5 photos originales comme benchmark principal ;
- utiliser les nouvelles photos comme vérité cachée/contrôle ;
- ne pas corriger la Scene manuellement grâce aux nouvelles photos ;
- améliorer le raisonnement générique pour savoir quand déduire, quand conserver l'incertitude et quand demander une vue supplémentaire.

## 16. Scenes consolidées locales

Des Scenes manuelles v5, v6 puis v7 ont été préparées pendant les conversations.

La v6 avait surtout élargi certains `access_spans` pour éviter qu'une volée débouche derrière un parapet après quantification.

La v7 ajoutait surtout les rattachements explicites au `volume_main` (`visibility.volume_id` et `Platform.host_volume_id`) sans modifier la géométrie architecturale.

Ces fichiers ne sont PAS garantis présents dans GitHub. Ne jamais prétendre les avoir. Les demander uniquement s'ils redeviennent nécessaires.

## 17. Interface utilisateur actuelle

Le parcours normal de `frontend/photo.html` est désormais beaucoup plus simple :
- 6 zones guidées de photos, chacune acceptant plusieurs images ;
- vues supplémentaires facultatives ;
- mesure/notes facultatives ;
- génération d'un paquet pour IA externe ;
- réimport d'un seul fichier JSON ;
- options techniques reléguées dans une zone avancée.

Le futur parcours direct par API est prévu visuellement mais n'est pas encore le parcours principal.

Important : vérifier les libellés exacts dans le code avant de guider l'utilisateur.

## 18. BUG / JALON ACTUEL : handoff vers IA externe

C'est le point exact où la conversation précédente s'est arrêtée.

Test utilisateur : il a pris les 5 photos originales + le ZIP `brickhouse-photos-a-analyser.zip` généré par BrickHouse et les a envoyés dans une conversation IA vierge.

L'IA a répondu en substance : « J'ai reçu les 5 photos et l'archive, dites-moi ce que vous souhaitez obtenir », au lieu d'exécuter automatiquement les instructions BrickHouse.

Diagnostic : le ZIP contenait déjà `00-LIRE-ET-ANALYSER.txt`, `manifest.json`, les prompts et les photos, mais une instruction enfermée dans un ZIP n'est pas nécessairement interprétée comme l'intention utilisateur principale par une IA externe.

Correction effectuée juste avant cette passation dans `frontend/photo-simple.js` :
- handoff passé conceptuellement à `handoff-0.3` ;
- instruction d'entrée renforcée : « INSTRUCTION PRINCIPALE — À EXÉCUTER IMMÉDIATEMENT » ;
- interdiction explicite de demander à l'utilisateur quel type d'analyse il souhaite ;
- ajout d'une courte consigne de lancement externe ;
- ajout dans le ZIP de `00-CONSIGNE-A-COLLER-DANS-LE-CHAT.txt` ;
- ajout de `manifest.launch_instruction` ;
- affichage dans l'interface d'un bloc « Message à envoyer avec le ZIP » ;
- tentative de copie automatique de cette consigne dans le presse-papiers ;
- statut après génération expliquant d'envoyer ZIP + message de lancement dans le même message.

Évolution suivante sur `main` :
- les 6 zones guidées acceptent maintenant plusieurs fichiers ;
- chaque photo reste une observation distincte dans le manifest avec `slot_view_index` ;
- plusieurs vues peuvent partager le même libellé sans que ce libellé force l'interprétation ;
- le paquet refuse plus de 12 photos au lieu de tronquer silencieusement les dernières ;
- tests dédiés ajoutés dans `tests/test_guided_multi_photo_slots.py`.

Tests frontend du handoff présents notamment dans `tests/test_external_ai_handoff_launch.py`.

Commits immédiatement précédant cette mise à jour :
- `7c05f8a6` — handoff externe plus explicite ;
- `4202ba73` — tests du handoff ;
- `49ea4042` — interface multi-photos par zone ;
- `9021bb0f` — conservation de toutes les vues dans le paquet IA ;
- `da03a75f` — tests de régression multi-photos.

Le statut CI distant doit toujours être vérifié avant de le déclarer vert.

## 19. Prochain test utilisateur EXACT

Après déploiement des derniers commits :
1. recharger complètement BrickHouse ;
2. utiliser uniquement les 5 photos originales ;
3. les classer dans les zones les plus proches sans chercher à faire correspondre artificiellement chaque photo à un libellé ; plusieurs photos peuvent être mises dans une même zone ;
4. pour le benchmark actuel : photo 1 en façade avant, photo 2 côté droit, photos 3 et 4 ensemble côté gauche, photo 5 en arrière / 3/4 arrière ;
5. générer un NOUVEAU paquet avec « Télécharger le paquet à envoyer à l'IA » ;
6. BrickHouse doit afficher « Message à envoyer avec le ZIP » ;
7. ouvrir une conversation IA vierge ;
8. joindre le nouveau ZIP ET envoyer dans le même message la consigne affichée par BrickHouse ;
9. ne rien ajouter sur l'architecture de la maison ;
10. si l'IA demande encore « que souhaitez-vous ? », récupérer sa réponse exacte : le handoff est encore insuffisant ;
11. si elle produit `brickhouse-external-result.json`, récupérer ce fichier sans le corriger manuellement et l'importer dans BrickHouse ;
12. ensuite analyser les éventuels refus Survey→Scene ou le rendu global.

## 20. Commits structurants récents à connaître

Cette liste est indicative ; toujours vérifier GitHub.

Parmi les commits mentionnés dans les conversations récentes :
- `aeb50628` généralisation du prompt au-delà de la maison test ;
- `c6d2e2c3`, `d0521f8b`, `8fb5f959` suppression de biais maison test dans les prompts ;
- `9fd2d568`, `13547932` encadrements architecturaux des fenêtres ;
- `b7b6eefe`, `c466aa65`, `f9387455` surfaces architecturales génériques ;
- `0b12bd7e` et suite : `fidelity_issues` ;
- `594d3e3f`, `52e96db6`, `45fd73cf` terrain/quantification ;
- `f5371dde`, `c44a9ea1`, `a229256a` fidélité des fenêtres ;
- `147605fd`, `726e5743`, `18163827`, `1b5cca6f` correction du chemin frontend vers `/api/v1/build-scene` ;
- `9e9abc74`, `6f9e4faa`, `c46c8d40` fixture Scene riche et smoke tests ;
- `d2da2a9f`, `82997645`, `0244e6c7` vues supplémentaires guidées ;
- `20bac3f6`, `342e95c8`, `0aa47808` raisonnement adaptatif et incertitude ;
- `aa6b4d3e`, `f350b6b1`, `d66d083a`, `0766c201`, `0c30fb19`, `bce83a5e` fidélité/incertitude dans export et viewer ;
- `7c05f8a6`, `4202ba73` handoff externe ;
- `49ea4042`, `9021bb0f`, `da03a75f` multi-photos par zone guidée.

## 21. Méthode de travail attendue

- Lire ce fichier puis inspecter GitHub.
- Modifier directement le dépôt quand nécessaire.
- Ne pas donner seulement du code à copier-coller si le changement peut être fait directement.
- Ajouter des tests de régression avec les changements de moteur/contrat.
- Mettre à jour prompts et interface lorsqu'un contrat évolue.
- Travailler plusieurs tâches cohérentes avant de revenir vers l'utilisateur.
- L'utilisateur préfère qu'on continue jusqu'à avoir réellement besoin de son intervention.
- Ne pas lui faire effectuer des tests après chaque petit commit.
- Quand son intervention devient nécessaire, donner des instructions extrêmement concrètes et vérifier d'abord les vrais libellés de l'interface.

## 22. Priorité de reprise

Priorité immédiate : **valider le nouveau handoff IA externe sur les 5 photos benchmark**, maintenant avec plusieurs photos possibles dans une même zone guidée, puis exploiter le résultat réel pour continuer le moteur.

Avant de solliciter l'utilisateur :
- inspecter les derniers fichiers `photo-simple.js`, `photo.html`, tests ;
- vérifier que les commits du handoff sont bien sur `main` ;
- vérifier CI/déploiement si les outils le permettent ;
- corriger toute incohérence détectée.

Ensuite seulement, demander le test décrit en section 19.

Après ce test, continuer en priorité sur :
- qualité du Survey généré depuis peu de vues ;
- refus des chaînes extérieures inventées ;
- raccord terrasse/escalier fondé sur preuves ;
- conservation stricte des ouvertures ;
- terrain/pente ;
- enrichissement prudent du catalogue de pièces LEGO ;
- trajectoire vers géométries polygonales/libres sans casser le pipeline courant.
