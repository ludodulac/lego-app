# Boldüngo / BrickHouse — idées produit en attente

Ce fichier conserve les idées utiles qui **ne font pas partie du chantier actif**. Il évite de mélanger exploration produit et progression technique vérifiée.

- `PROGRESSION.md` reste la source de vérité opérationnelle : état réel, priorités actives et ordre de travail.
- Les issues/PR décrivent un travail concret en cours ou prêt à être réalisé.
- Les ADR figent une décision d'architecture suffisamment mûre.
- `PRODUCT_IDEAS.md` conserve les concepts à ne pas perdre mais qui ne doivent pas détourner le chantier actif.

Une idée quitte ce fichier seulement lorsqu'elle a un besoin utilisateur suffisamment clair, un périmètre décidé et une priorité explicite. Elle est alors promue vers `PROGRESSION.md` et une issue ; une décision structurante peut ensuite nécessiter un ADR.

## En attente — reconstruction de façade seule / appartement en façade

**Statut : PARKED / NON ACTIF.** Ne pas ouvrir de chantier d'implémentation tant que le flux principal maison complète n'a pas atteint la fidélité attendue.

Cas envisagé : l'utilisateur ne veut pas reconstruire un bâtiment entier mais seulement une façade, par exemple la façade d'un appartement au milieu d'un immeuble ou d'un alignement de maisons.

Piste de représentation finale : une façade LEGO autonome pouvant être présentée dans un cadre/display plutôt qu'un faux bâtiment 3D complété avec des côtés et un arrière inventés.

Questions produit futures que l'IA pourrait poser après analyse des photos :

- Quel appartement/étage ou quelle zone de façade veux-tu conserver ?
- Faut-il inclure les façades voisines visibles à gauche/droite ?
- Faut-il inclure les niveaux au-dessus et/ou en dessous ?
- Veux-tu uniquement la façade sélectionnée dans un cadre/display ?

Principe à préserver : les parties hors périmètre peuvent être analysées comme contexte pour comprendre les occlusions et la géométrie, sans être reproduites dans le modèle final.

Cette idée est distincte de l'exigence générale de **reconstruction intent / target scope** : le logiciel doit savoir ce que l'utilisateur veut reconstruire et pouvoir demander une clarification quand ce périmètre est ambigu. Cette exigence générale peut progresser avec le pipeline principal ; le produit spécialisé « façade encadrée » reste différé.

## Rappels produit à conserver lors des futures explorations

- Comprendre et associer les objets entre les vues avant de les styliser en LEGO.
- Distinguer bâtiment cible, contexte et ownership incertain ; un objet du voisinage ne devient pas un objet de la cible par simple présence dans l'image.
- Une fois un objet correctement compris, autoriser une stylisation bornée : par exemple réduire le nombre de lattes d'une terrasse tout en conservant son emprise, son niveau, son garde-corps et sa structure caractéristique.
- Ne pas simplifier les traits identitaires : embrasures/retraits importants, porte-fenêtre jusqu'au sol, volumes/paliers, topologie d'escalier, débords de toiture et autres particularités géométriques établies.
- Les détails secondaires (gouttières, jardinières, végétation caractéristique, mobilier extérieur) peuvent être différés ou simplifiés sans bloquer la vérité architecturale principale.
