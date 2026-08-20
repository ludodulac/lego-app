# BrickHouse — principes de notice de montage

La notice doit devenir de plus en plus proche d'une excellente notice de construction dans son usage, sans copier une marque ni un habillage graphique propriétaire.

Principes :

- une étape = une action visuelle courte et compréhensible ;
- limiter le nombre de nouvelles pièces par étape quand un niveau contient beaucoup de placements ;
- toujours montrer clairement les pièces à ajouter et leur quantité ;
- atténuer le déjà-monté et mettre en évidence uniquement les nouvelles pièces ;
- conserver une orientation stable tant que possible, mais choisir la façade pertinente quand une étape travaille une autre face ;
- murs avant détails ; toiture après façades ;
- une fenêtre réelle peut devenir un sous-assemblage cadre + vitrage avant son insertion dans la maison ;
- grande illustration centrale, peu de texte, numéro d'étape immédiatement repérable ;
- utiliser des flèches de pose quand leur nombre reste lisible ;
- afficher explicitement une rotation de maquette seulement lorsque l'angle change réellement ;
- afficher une rotation de pièce lorsqu'elle n'est pas dans son orientation canonique ;
- utiliser une vue rapprochée pour fenêtres, détails de façade et autres fixations difficiles à lire ;
- organiser le montage en phases et sachets virtuels pour préparer seulement les pièces nécessaires au prochain bloc ;
- impression A4 : une étape par page et une page de séparation claire pour chaque nouvelle phase ;
- les pièces représentées doivent rester celles du BrickModel/BOM, jamais des équivalents graphiques inventés.

## Grammaire de montage actuelle

1. **Structure** — murs, du bas vers le haut.
2. **Fenêtres** — sous-assemblages cadre + vitrage quand la compatibilité a été validée, puis insertion.
3. **Façades** — appuis, entourages et détails complémentaires.
4. **Toiture** — pans puis faîtage, après fermeture des façades.

Chaque phase reçoit un **sachet virtuel**. Ce sachet n'affirme pas qu'un fournisseur livrera physiquement les pièces ainsi : c'est une aide de préparation produite par BrickHouse.

## Prochaines améliorations

- vraie vue éclatée dédiée aux sous-assemblages complexes ;
- appels de zoom reliés par un repère numéroté sur l'image principale ;
- contrôle automatique de difficulté et découpage plus fin des étapes ambiguës ;
- détection de pièces masquées afin de choisir une autre caméra avant impression ;
- inventaire détaillé par sachet avec contrôle de quantité avant de commencer la phase.
