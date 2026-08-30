# Boldüngo — passe de raisonnement architectural avant sérialisation

## But

La conversion Survey → Scene ne doit plus demander à l’IA de passer directement de la reconnaissance visuelle au JSON final. Une étape de raisonnement architectural explicite doit précéder toute sérialisation.

## 1. Compréhension de l’objet

Pour chaque objet certain/plausible du Survey :
- identifier sa nature architecturale ;
- retrouver le même objet dans toutes les vues pertinentes ;
- distinguer les parties visibles, occultées et ambiguës ;
- identifier ses relations physiques avec bâtiment, sol, plateformes, escaliers et volumes voisins.

Pour un escalier : déterminer le sens de montée, l’extrémité basse, l’extrémité haute, la surface du bâtiment ou de la plateforme reçue à l’arrivée, et les indices visibles de marches, contremarches, murs latéraux et niveaux.

## 2. Hypothèses géométriques

Ne pas choisir immédiatement une coordonnée unique. Construire d’abord des intervalles/hypothèses compatibles avec :
- perspective et lignes de fuite ;
- coins et arêtes partagés ;
- alignements verticaux/horizontaux ;
- répétitions d’ouvertures et niveaux ;
- dimensions utilisateur connues ;
- mêmes objets vus sous plusieurs angles.

Les références usuelles d’objets architecturaux peuvent fournir uniquement des plages plausibles secondaires. Elles ne remplacent jamais les preuves de la maison photographiée.

## 3. Résolution conjointe

Les objets liés physiquement sont résolus ensemble. Une relation `connects_to` certaine est une contrainte du système géométrique, pas une annotation à recopier après coup.

Exemple escalier → bâtiment : l’extrémité haute, le mur receveur, le niveau d’arrivée et la position du bâtiment doivent être compatibles simultanément. Il est interdit d’estimer l’escalier et le bâtiment séparément puis de déclarer la relation `resolved` si leurs métriques ne se touchent pas.

## 4. Audit contradictoire

Avant sérialisation, rechercher activement les contradictions :
- relation dite résolue mais contact métrique absent ;
- ouverture hors de sa façade ;
- objets qui se chevauchent sans relation ;
- niveaux incompatibles entre vues ;
- échelle locale incohérente avec l’ancre utilisateur ;
- hypothèse sémantique incompatible avec la géométrie.

Toute contradiction doit être corrigée par une nouvelle résolution des seules valeurs `inferred`, ou laissée `unresolved` si elle n’est pas défendable. Ne jamais faire passer le validateur par snapping arbitraire.

## 5. Sérialisation seulement en dernier

Le JSON ArchitecturalScene v0.2 est la sortie d’un raisonnement déjà cohérent. Les champs `geometry_status:"resolved"` et `semantic_anchor_volume_id` ne sont autorisés qu’après vérification numérique finale des contraintes backend.

## 6. Une photo vs plusieurs photos

Avec une seule photo, conserver davantage d’intervalles, de faibles confiances et d’inconnues. Avec plusieurs photos, utiliser les vues comme contraintes croisées pour réduire progressivement ces intervalles. Les vues ne sont pas des estimations indépendantes : elles décrivent une seule scène physique commune.
