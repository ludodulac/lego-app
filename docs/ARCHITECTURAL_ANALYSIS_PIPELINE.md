# BrickHouse — pipeline d'analyse architecturale

## Principe

BrickHouse ne doit pas demander à une IA de transformer directement des pixels en briques LEGO. L'analyse photo est divisée en passes avec des responsabilités distinctes.

## Passe A — compréhension contextuelle / sémantique

But : comprendre ce que représentent les formes visibles sans encore les convertir en mesures définitives.

Cette passe identifie notamment :
- bâtiment principal, extensions, garages, tours, terrasses et volumes secondaires ;
- façades et coins visibles ;
- fenêtres, portes, bow-windows, balcons, cheminées, lucarnes, corniches ;
- familles de toiture et relations entre pans ;
- répétitions et symétries probables ;
- matériaux et changements de surface utiles à la compréhension ;
- occultations, végétation, zones non visibles et ambiguïtés ;
- hypothèses contextuelles possibles, avec confiance explicite.

Exemple : reconnaître qu'une masse vitrée en saillie est probablement un bow-window peut aider à ne pas l'interpréter comme un second bâtiment indépendant.

Cette passe produit des hypothèses, jamais des dimensions métriques non justifiées.

## Passe B — reconstruction géométrique / structurelle

But : transformer les observations en géométrie cohérente.

Elle doit :
- corriger les effets de perspective ;
- rechercher axes, lignes de fuite, verticales et horizontales architecturales ;
- comparer les rapports de distances sur une même façade ;
- croiser plusieurs vues d'un même coin/volume ;
- estimer largeur, profondeur, hauteur, rotations et décalages relatifs ;
- placer ouvertures et détails par coordonnées/ratios ;
- exploiter toute mesure réelle fournie comme ancre d'échelle globale ;
- conserver `null` lorsqu'une valeur ne peut pas être estimée honnêtement ;
- associer provenance et confiance à chaque valeur importante.

Une interprétation issue de la passe A ne devient une mesure que si la géométrie, une autre vue ou une information utilisateur la soutient.

## Passe C — BrickHouse Architectural Scene (cible)

Le résultat général doit évoluer vers une scène paramétrique composable, plus générale que le BuildingModel M0.

Concepts cibles :
- noeuds de volume : box, prism, cylinder, extrusion, roof surface et éventuellement forme libre contrôlée ;
- transformation : position XYZ, rotation XYZ, échelle/dimensions ;
- relations : attached_to, rests_on, intersects, subtracts, aligned_with, repeated_from ;
- ouvertures et éléments architecturaux attachés à une surface ;
- surfaces/matériaux séparés de la géométrie ;
- valeurs inconnues autorisées ;
- provenance (`observed`, `user_provided`, `inferred`, `estimated`) ;
- confiance par propriété ;
- preuves géométriques ou sémantiques associées.

Le BuildingModel actuel reste un sous-ensemble volontaire de cette scène, utilisé pour le MVP simple.

## Passe D — normalisation vers les capacités LEGO

La scène architecturale est ensuite transformée vers la meilleure approximation que le moteur LEGO sait réellement construire au niveau de fidélité/format demandé.

Règles :
- ne jamais modifier silencieusement l'architecture pour la rendre compatible ;
- distinguer représentation fidèle, simplification explicite et élément non supporté ;
- bloquer la génération si une simplification changerait fondamentalement le bâtiment ;
- conserver les éléments non construits dans la scène pour les futures versions du moteur.

## Pourquoi deux analyses IA

Une lecture purement géométrique peut mal interpréter une forme faute de contexte. Une lecture purement sémantique peut reconnaître correctement « une tour » ou « un bow-window » mais inventer ses dimensions. Les deux passes se contrôlent mutuellement :

**contexte pour comprendre la forme → géométrie pour la quantifier → validation croisée → scène paramétrique.**

Cette séparation est une règle d'architecture BrickHouse, indépendante du fournisseur (Gemini, OpenAI ou autre).