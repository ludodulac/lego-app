# Boldüngo — Dossier juridique et commercial : LEGO, briques compatibles et vente

> **Document stratégique — France / Union européenne — état de l'analyse : 27 août 2026.**
>
> Ce document synthétise les recherches juridiques et les choix commerciaux envisagés pour Boldüngo. Il ne remplace pas une consultation d'avocat. Les points signalés comme « à valider » doivent être vérifiés avant commercialisation.

## 1. Résumé exécutif

Boldüngo doit être conçu comme une plateforme indépendante capable de transformer les photographies d'une maison en un modèle 3D constructible avec des briques à tenons, puis de produire :

- une visualisation 3D ;
- une nomenclature exacte (BOM) ;
- une notice interactive ;
- une notice PDF imprimable ;
- des listes d'approvisionnement adaptées à plusieurs fournisseurs ;
- éventuellement, plus tard, une notice imprimée et/ou un kit physique.

La stratégie recommandée est de **ne pas commencer comme fabricant/importateur de briques**. Boldüngo doit d'abord gagner de l'argent sur la conception et la notice, puis sur l'apport de commandes à plusieurs fournisseurs.

Architecture commerciale recommandée :

`Photos -> modèle Boldüngo -> BOM abstraite -> notice -> mappings fournisseurs -> choix LEGO / X / Y -> vente des briques par le fournisseur -> commission Boldüngo`

Le principe central est : **Boldüngo peut être compatible avec LEGO sans être LEGO.**

---

## 2. Séparer Boldüngo de LEGO

Boldüngo doit posséder sa propre marque, son logo, son identité visuelle, ses notices et son catalogue interne.

Le nom et le logo LEGO ne doivent jamais être utilisés de manière à faire croire que Boldüngo est un produit officiel, licencié, sponsorisé ou approuvé par le LEGO Group.

Une formulation de compatibilité peut être envisageable lorsque LEGO est utilisé uniquement pour identifier la destination ou la compatibilité des pièces, sous réserve d'un usage honnête au sens du droit européen des marques.

Exemple à faire valider juridiquement :

> « LEGO® est une marque du LEGO Group. Boldüngo est une marque indépendante et n'est ni affiliée, ni sponsorisée, ni autorisée, ni approuvée par le LEGO Group. Les références à LEGO® servent uniquement à indiquer la compatibilité de certains éléments. »

À éviter : « maison LEGO Boldüngo », « Boldüngo LEGO », reproduction du logo LEGO ou packaging imitant fortement l'identité LEGO.

Sources principales :
- Règlement (UE) 2017/1001 sur la marque de l'Union européenne, notamment les limites permettant certains usages référentiels de la marque.
- LEGO Fair Play : https://www.lego.com/legal/notices-and-policies/fair-play
- LEGO Intellectual Property Notice : https://www.lego.com/legal/notices-and-policies/intellectual-property-notice

---

## 3. Brevets, dessins et autres droits sur les pièces

L'expiration des anciens brevets relatifs au système historique de briques à tenons **ne signifie pas que toutes les pièces LEGO peuvent être copiées**.

Il faut analyser séparément :

1. brevets techniques ;
2. dessins et modèles ;
3. droit d'auteur ;
4. marques tridimensionnelles ou autres marques ;
5. concurrence déloyale/parasitisme selon le contexte ;
6. droits contractuels sur les catalogues, données et fichiers numériques.

Le brevet historique relatif au principe d'assemblage est expiré. En revanche, la jurisprudence européenne récente confirme que certains dessins LEGO peuvent encore bénéficier d'une protection, notamment dans le contexte des systèmes modulaires.

Références importantes :
- Tribunal UE, T-515/19 ;
- Tribunal UE, T-537/22 ;
- CJUE, C-211/24, LEGO / Pozitív Energiaforrás, 4 septembre 2025.

Conséquence produit : créer un registre de clearance IP par géométrie.

Exemple :

`BOLDUNGO_PART_ID -> géométrie -> droits potentiels -> territoires -> fournisseurs -> LEGO Design ID -> BrickLink ID -> statut vert/orange/rouge`

Les figurines, personnages, impressions, décorations et pièces spécialisées récentes doivent être considérés comme plus risqués que les briques architecturales élémentaires.

---

## 4. Catalogue géométrique indépendant

Le choix architectural déjà retenu dans le projet est le bon : le moteur ne doit pas dépendre d'un fabricant.

Exemple :

`BRICK_2X4_WHITE`

avec :
- dimensions ;
- connecteurs ;
- collisions ;
- couleur ;
- contraintes de construction.

Puis, dans une couche séparée :

`BRICK_2X4_WHITE -> LEGO reference / BrickLink ID / Supplier X SKU / Supplier Y SKU`

Ainsi, la BOM principale Boldüngo reste stable même si un fournisseur change une référence, une couleur, un prix ou une disponibilité.

Il est recommandé de produire les meshes du viewer indépendamment, sans reprendre automatiquement les fichiers propriétaires d'un fabricant et sans reproduire les marquages LEGO sur les tenons.

---

## 5. La BOM est un actif central de Boldüngo

Pour chaque maison, Boldüngo doit générer une nomenclature universelle exacte.

Exemple :

| Pièce Boldüngo | Qté | LEGO | Fournisseur X | Fournisseur Y |
|---|---:|---|---|---|
| Brique 2x4 blanche | 120 | mapping LEGO | SKU-X | SKU-Y |
| Brique 1x2 blanche | 84 | mapping LEGO | SKU-X | SKU-Y |
| Pente 2x2 noire | 42 | mapping LEGO | SKU-X | SKU-Y |

La notice explique **comment construire**.

La BOM explique **ce qu'il faut acheter**.

La couche fournisseur explique **où l'acheter**.

Il vaut mieux conserver les mappings et disponibilités fournisseurs en ligne plutôt que de les figer définitivement dans la notice imprimée. Un QR code dans la notice peut renvoyer vers une page Boldüngo donnant les options d'approvisionnement à jour.

---

## 6. LEGO, BrickLink et automatisation des commandes

### LEGO

LEGO dispose d'un programme officiel d'affiliation LEGO.com permettant à des partenaires acceptés de percevoir une commission sur certaines ventes attribuées.

Source : https://www.lego.com/fr-fr/page/affiliate-program

Cela ne signifie pas automatiquement que Boldüngo est autorisé à remplir programmatiquement un panier Pick a Brick avec plusieurs centaines ou milliers de pièces. Aucune API publique générale Pick a Brick destinée à ce cas d'usage n'a été identifiée dans les recherches effectuées.

La bonne stratégie est donc :

1. générer la liste LEGO précise ;
2. utiliser les mécanismes officiellement autorisés ;
3. demander à LEGO une intégration B2B permettant idéalement le préremplissage de la commande ;
4. ne pas scraper ou automatiser LEGO.com sans autorisation.

### BrickLink

BrickLink dispose d'une API officielle, principalement orientée vers la gestion programmatique des boutiques et les données associées.

Source : https://www.bricklink.com/v2/api/welcome.page

Les conditions BrickLink limitent notamment certains usages automatisés et la redistribution de données. Il ne faut donc pas construire le catalogue Boldüngo en scrapant BrickLink.

Sources :
- https://www.bricklink.com/v2/api/welcome.page
- https://v2.bricklink.com/en-us/terms-of-service

BrickLink possède également un Designer Program, qui montre qu'il existe déjà un écosystème officiel associant conception, instructions et listes de pièces.

Source : https://www.bricklink.com/v3/designer-program/main.page

### BrickLink Studio

Ne pas considérer la bibliothèque Studio comme une bibliothèque libre réutilisable automatiquement dans Boldüngo. Vérifier les licences avant toute incorporation de meshes, données ou exécution serveur.

---

## 7. Modèle économique recommandé

### Produit Boldüngo

Boldüngo vend la transformation :

`photos -> reconstruction -> modèle en briques -> BOM -> notice`

Exemple commercial :

- aperçu 3D gratuit ou partiel ;
- modèle standard : prix à tester, par exemple 29–49 € ;
- modèle détaillé : 49–79 € ;
- premium avec correction humaine : prix supérieur ;
- notice interactive incluse ;
- PDF imprimable ;
- impression physique en option.

Les prix sont des hypothèses à tester, pas des recommandations tarifaires définitives.

### Deuxième revenu : commissions sur les briques

Le même projet peut ensuite générer une commission lorsque le client achète les pièces.

Exemple :

| Option | Rôle |
|---|---|
| LEGO officiel | fournisseur officiel / affiliation ou futur partenariat |
| Fournisseur X | briques compatibles, vente directe au client |
| Fournisseur Y | briques compatibles, vente directe au client |
| Déjà propriétaire des pièces | téléchargement de la BOM |

Boldüngo peut en principe travailler avec plusieurs fournisseurs et percevoir des commissions différentes, sous réserve des contrats conclus avec chacun et d'éventuelles clauses d'exclusivité.

---

## 8. Le modèle d'intermédiation recommandé

Pour réduire la charge liée aux produits physiques, le parcours initial recommandé est :

1. le client achète à Boldüngo le service de conception ;
2. Boldüngo produit la BOM ;
3. Boldüngo affiche plusieurs offres de fournisseurs ;
4. le client choisit son fournisseur ;
5. **le fournisseur vend juridiquement les briques au client** ;
6. le fournisseur encaisse le prix des briques ;
7. le fournisseur prépare et expédie la commande ;
8. Boldüngo reçoit une commission selon son accord avec le fournisseur.

L'interface doit indiquer clairement « vendu et expédié par Fournisseur X » lorsque c'est effectivement le cas.

Il ne suffit pas d'appeler une opération « dropshipping » pour transférer la responsabilité. Si Boldüngo est juridiquement le vendeur des briques, il conservera les obligations correspondantes même si un tiers expédie le colis.

À faire valider par avocat : qualification exacte de Boldüngo (apporteur, affilié, intermédiaire, marketplace, vendeur) selon le parcours contractuel et de paiement retenu.

---

## 9. Fournisseurs X et Y

Un partenaire idéal devrait :

- disposer d'une large gamme de briques compatibles ;
- être capable de fournir les pièces à l'unité et dans les bonnes couleurs ;
- accepter une BOM générée automatiquement ;
- disposer idéalement d'une API ;
- préparer une commande personnalisée de plusieurs centaines/milliers de pièces ;
- éventuellement trier les pièces en sachets numérotés ;
- vendre directement au consommateur ;
- expédier directement ;
- gérer SAV/retours relatifs aux briques ;
- disposer d'une conformité UE documentée ;
- accepter de verser une commission à Boldüngo.

Le scénario idéal est :

`Boldüngo BOM -> API X -> panier/commande X -> paiement X -> préparation X -> expédition X -> commission Boldüngo`

Il est préférable, au début, de travailler avec un opérateur européen ou avec une chaîne dont l'opérateur économique responsable dans l'UE et la conformité sont clairement établis.

---

## 10. Pourquoi éviter de devenir immédiatement vendeur/importateur

Si Boldüngo achète/importе des briques hors UE et les revend sous sa marque, les obligations augmentent fortement.

Selon la qualification du produit et le rôle de Boldüngo, il faut notamment étudier :

- sécurité des jouets ;
- marquage CE ;
- normes EN 71 applicables ;
- REACH ;
- GPSR (règlement UE 2023/988) ;
- avertissements d'âge ;
- traçabilité et lots ;
- dossier technique ;
- déclaration UE de conformité ;
- rappels et incidents ;
- responsabilité produit ;
- REP jouets et emballages en France ;
- obligations de l'importateur.

Le nouveau règlement (UE) 2025/2509 relatif à la sécurité des jouets a été adopté et doit être anticipé dans la roadmap réglementaire, avec application prévue à compter du 1er août 2030 après la transition.

Le simple fait qu'un fournisseur affirme qu'un produit est « CE » ne doit pas être considéré comme suffisant lorsque Boldüngo devient lui-même l'opérateur responsable pertinent.

---

## 11. Notice numérique et notice imprimée

La notice est un produit Boldüngo important et peut être proposée sous plusieurs formes.

### Notice interactive

Sur téléphone, tablette ou ordinateur :

- étapes numérotées ;
- modèle 3D rotatif ;
- zoom ;
- pièces nécessaires pour l'étape ;
- progression ;
- possibilité de masquer les étapes précédentes.

### PDF

Un PDF imprimable peut être inclus ou réservé à une formule supérieure.

### Impression à la demande

Boldüngo peut proposer une option payante de notice imprimée et sous-traiter l'impression et l'expédition à un imprimeur à la demande.

Cela évite d'avoir une infrastructure d'impression interne.

---

## 12. Photographies, maisons et propriété intellectuelle du résultat

Les photos envoyées par les utilisateurs peuvent être protégées par droit d'auteur et constituer des données personnelles.

Les CGU doivent prévoir que le client :

- a le droit de transmettre les photographies ;
- accorde à Boldüngo une licence limitée aux traitements nécessaires au service ;
- garantit raisonnablement qu'il dispose des droits nécessaires sur les contenus transmis.

Boldüngo doit conserver ses droits sur :

- son logiciel ;
- ses algorithmes ;
- son catalogue ;
- ses templates ;
- ses composants génériques ;
- son savoir-faire.

Le client doit obtenir des droits suffisamment larges sur son résultat personnalisé pour pouvoir consulter, imprimer et utiliser la notice et construire son modèle, sous réserve des droits de tiers.

Les bâtiments célèbres ou architectures originales encore protégées doivent faire l'objet d'un traitement spécifique. En France, l'exception de panorama est limitée et ne doit pas être considérée comme une autorisation générale de commercialiser des reproductions de toute architecture protégée.

---

## 13. RGPD et photos de maisons privées

Les photos d'une maison peuvent révéler :

- personnes ;
- adresse/localisation ;
- plaques d'immatriculation ;
- objets personnels ;
- intérieur du domicile ;
- systèmes de sécurité ;
- métadonnées GPS/EXIF.

Principe recommandé :

`upload -> traitement -> modèle -> livraison -> suppression programmée des originaux`

La conservation doit être limitée à ce qui est nécessaire.

Il faut séparer juridiquement et techniquement :

1. l'utilisation des photos nécessaire pour produire la commande ;
2. une éventuelle utilisation ultérieure pour entraîner ou améliorer une IA.

Ne pas considérer automatiquement que les photos fournies pour une commande peuvent servir à l'entraînement des modèles.

Sources principales : CNIL, recommandations relatives au développement des systèmes d'IA et au RGPD : https://www.cnil.fr/fr/developpement-des-systemes-dia-les-recommandations-de-la-cnil-pour-respecter-le-rgpd

Une AIPD doit être examinée selon la configuration finale du traitement.

---

## 14. IA : rôle recommandé

L'IA ne devrait pas générer directement et sans contrôle une liste de briques réputée constructible.

Pipeline recommandé :

`photos -> reconstruction IA -> représentation architecturale structurée -> moteur géométrique déterministe -> moteur briques -> vérification collisions/connexions/stabilité -> BOM -> AssemblyPlan`

Le système doit pouvoir détecter ou signaler :

- parties invisibles ;
- faible confiance ;
- géométrie inventée ;
- incohérences ;
- impossibilités de construction.

Cette approche est cohérente avec l'architecture actuelle du dépôt.

---

## 15. Les cinq architectures commerciales

### A — Notice uniquement

**Autorisé en principe :** vendre la conception, le modèle, la BOM et la notice originale.

**Contraintes :** IP des bâtiments/photos, RGPD, marque LEGO, droit de la consommation numérique.

**Complexité : faible à modérée.**

**Recommandation : excellente V1.**

### B — Notice + redirection/affiliation

Boldüngo fournit la BOM et redirige vers LEGO, BrickLink ou partenaires.

**Contraintes :** respecter les programmes et CGU ; ne pas scraper ; ne pas automatiser un checkout sans autorisation.

**Complexité : modérée.**

**Recommandation : meilleur modèle initial avec A.**

### C — Marketplace/intermédiation

Boldüngo héberge plusieurs vendeurs ou organise plus directement la transaction.

**Contraintes supplémentaires :** DSA, obligations marketplace, sécurité produit, informations vendeurs, paiements et consommation.

**Complexité : élevée.**

**Recommandation : phase ultérieure.**

### D — Kit physique Boldüngo

Boldüngo vend le kit complet sous sa marque.

**Contraintes :** clearance IP pièce par pièce + sécurité/conformité + import + REP + responsabilité produit.

**Complexité : élevée.**

**Recommandation : intéressante lorsque le volume justifie l'infrastructure réglementaire.**

### E — partenariat officiel LEGO/BrickLink

Objectif : négocier catalogue, API, deep links, Wanted Lists, Pick a Brick, attribution commerciale et éventuellement droits d'utilisation de certaines données/assets.

**Complexité juridique après accord : relativement maîtrisable ; difficulté principale commerciale/négociation.**

**Recommandation : poursuivre en parallèle sans rendre la V1 dépendante d'un accord.**

---

## 16. Roadmap commerciale recommandée

### Phase 1 — Boldüngo Design

Le client paie pour : modèle + BOM + notice.

Objectif : prouver que des clients sont prêts à payer pour « ma maison en briques ».

Une correction humaine des modèles peut être utilisée au début si l'IA n'est pas parfaite.

### Phase 2 — Boldüngo Source

Ajouter :

- mappings fournisseurs ;
- comparaison disponibilité/prix ;
- exports de listes ;
- affiliation ;
- commissions.

### Phase 3 — intégrations officielles

Négocier avec LEGO, BrickLink et fournisseurs compatibles :

- API ;
- paniers préremplis ;
- transfert de BOM ;
- commissions ;
- accès/licence catalogue.

### Phase 4 — Boldüngo Kit

Seulement lorsque les volumes justifient le coût réglementaire :

- fournisseur audité ;
- clearance IP ;
- essais ;
- conformité ;
- packaging ;
- logistique.

### Phase 5 — international

Créer une matrice juridique par territoire. Une pièce utilisable en UE n'est pas automatiquement libre de risques dans tous les pays.

---

## 17. Exemple de parcours client cible

1. « Photographiez votre maison ».
2. Boldüngo reconstruit le bâtiment.
3. Le client voit un aperçu 3D en briques.
4. Il choisit taille/détail.
5. Il achète la conception Boldüngo.
6. Il reçoit notice interactive + PDF + BOM.
7. Boldüngo affiche :
   - « J'ai déjà mes briques » ;
   - « Pièces LEGO officielles » ;
   - « Fournisseur X — compatible » ;
   - « Fournisseur Y — compatible premium ».
8. La disponibilité est calculée depuis les mappings fournisseurs.
9. Le client choisit.
10. Lorsque possible, la BOM est transférée au fournisseur via une intégration autorisée.
11. Le fournisseur vend et expédie les briques.
12. Boldüngo reçoit sa commission.
13. Le client construit en suivant l'application ou la notice papier.

---

## 18. Positionnement commercial

Le principal actif de Boldüngo n'est pas la brique elle-même.

La promesse est :

> « Je photographie ma maison et Boldüngo transforme automatiquement ce bâtiment en un modèle réellement constructible, puis me dit exactement quelles pièces acheter et où les trouver. »

Boldüngo peut ainsi devenir une couche de conception et d'approvisionnement multi-fournisseurs plutôt qu'un simple fabricant de briques.

Cette indépendance permet aussi de négocier plus tard avec LEGO à partir d'une position plus forte : Boldüngo peut démontrer qu'il génère une nouvelle demande de pièces officielles sans dépendre techniquement d'elles.

---

## 19. Checklist avant lancement commercial

### Marque / IP

- [ ] Recherche d'antériorités BOLDÜNGO INPI/EUIPO.
- [ ] Dépôt de marque et logo.
- [ ] Validation juridique du disclaimer LEGO.
- [ ] Validation des formulations « compatible avec LEGO® ».
- [ ] Catalogue géométrique interne indépendant.
- [ ] Registre IP pièce par pièce.
- [ ] Clearance dessins/brevets des pièces du catalogue initial.
- [ ] Provenance documentée des meshes et données.
- [ ] Exclusion initiale des figurines et pièces à haut risque.

### LEGO / BrickLink / fournisseurs

- [ ] Candidature affiliation LEGO.
- [ ] Contact B2B LEGO / Pick a Brick.
- [ ] Contact BrickLink concernant intégrations et droits de données.
- [ ] Aucun scraping non autorisé.
- [ ] Contrats fournisseur X/Y.
- [ ] Définition des commissions.
- [ ] Vérification des clauses d'exclusivité.
- [ ] Définition claire du vendeur des briques dans le parcours utilisateur.

### RGPD

- [ ] Cartographie des traitements.
- [ ] Bases juridiques.
- [ ] Politique de confidentialité.
- [ ] Durées de conservation.
- [ ] Suppression automatisée des photos originales lorsque possible.
- [ ] Gestion EXIF/GPS.
- [ ] DPA fournisseurs cloud/IA.
- [ ] Analyse transferts hors EEE.
- [ ] Étude AIPD.
- [ ] Séparation production / entraînement IA.

### Vente numérique

- [ ] CGU.
- [ ] CGV.
- [ ] Règles de rétractation/contenu numérique.
- [ ] Droits du client sur son modèle et sa notice.
- [ ] Garanties du client concernant les photos et l'architecture.

### Si kits physiques

- [ ] Qualification jouet.
- [ ] Rôle fabricant/importateur/distributeur.
- [ ] EN 71 applicable.
- [ ] REACH.
- [ ] GPSR.
- [ ] CE.
- [ ] Dossier technique.
- [ ] Déclaration UE de conformité.
- [ ] Traçabilité/lot.
- [ ] Avertissements.
- [ ] Procédure rappel.
- [ ] Assurance responsabilité produit.
- [ ] REP jouets et emballages / IDU France.
- [ ] Audit fournisseur.
- [ ] Anticipation du règlement UE 2025/2509.

---

## 20. Questions impératives pour l'avocat spécialisé

1. Quelles géométries du catalogue initial sont encore couvertes par des dessins, brevets ou autres droits pertinents dans l'UE ?
2. Quelle formulation exacte utiliser pour « compatible avec LEGO® » et le disclaimer ?
3. Quels Design IDs, Element IDs, BrickLink IDs et autres données peuvent être stockés/affichés commercialement ?
4. Quelles données/API LEGO et BrickLink peuvent être utilisées et redistribuées dans Boldüngo ?
5. Dans le parcours fournisseur X/Y envisagé, Boldüngo est-il apporteur d'affaires, intermédiaire, marketplace ou vendeur ?
6. Quelles obligations subsistent pour Boldüngo lorsque le fournisseur vend et expédie directement les briques ?
7. Comment rédiger les clauses relatives aux photographies, architectures et modèles générés ?
8. Quelle base RGPD retenir pour le traitement des photos et, séparément, pour une éventuelle amélioration de l'IA ?
9. À partir de quel parcours commercial Boldüngo devient-il fabricant/importateur/distributeur au sens des réglementations produit ?
10. Quel régime exact appliquer à un éventuel kit 14+/adulte et quand reste-t-il juridiquement un jouet ?

---

## 21. Sources de référence à maintenir à jour

Sources primaires/prioritaires :

- EUR-Lex — règlement marque UE 2017/1001 : https://eur-lex.europa.eu/
- EUR-Lex — dessins et modèles : https://eur-lex.europa.eu/
- EUR-Lex — GPSR 2023/988 : https://eur-lex.europa.eu/eli/reg/2023/988/oj
- EUR-Lex — AI Act 2024/1689 : https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- EUR-Lex — règlement jouets 2025/2509 : https://eur-lex.europa.eu/eli/reg/2025/2509/oj
- EUIPO : https://www.euipo.europa.eu/
- CJUE/Curia : https://curia.europa.eu/
- INPI : https://www.inpi.fr/
- CNIL : https://www.cnil.fr/
- DGCCRF : https://www.economie.gouv.fr/dgccrf
- LEGO Legal : https://www.lego.com/legal
- LEGO Affiliate Program : https://www.lego.com/fr-fr/page/affiliate-program
- BrickLink API : https://www.bricklink.com/v2/api/welcome.page
- BrickLink Terms : https://v2.bricklink.com/en-us/terms-of-service
- BrickLink Designer Program : https://www.bricklink.com/v3/designer-program/main.page

---

## Conclusion

La stratégie recommandée est de construire Boldüngo comme **le cerveau indépendant de la construction personnalisée en briques** :

`maison -> modèle -> BOM -> notice -> comparaison des fournisseurs -> achat`

La V1 doit monétiser la conception et la notice. La V2 doit ajouter les commissions d'approvisionnement. La vente directe de kits Boldüngo peut venir plus tard lorsque le volume économique justifie les obligations de conformité et de responsabilité produit.

Le catalogue abstrait multi-fournisseurs est la décision architecturale la plus importante : il permet à Boldüngo de travailler avec LEGO, BrickLink, des fabricants compatibles et les briques déjà possédées par le client sans rendre le produit dépendant d'une seule marque.