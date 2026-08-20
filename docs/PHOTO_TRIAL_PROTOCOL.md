# BrickHouse — protocole du premier essai photo réel

Ce document définit le premier essai utilisateur du MVP photo. Il doit rester simple et reproductible : le but n'est pas encore de tester toutes les architectures, mais de vérifier le parcours complet **photos -> BuildingModel -> validation -> LEGO -> viewer/BOM/notice**.

## 1. Maison à choisir pour le premier essai

Choisir volontairement une maison dans le domaine M0 :
- un volume principal rectangulaire ;
- un toit à deux pans clairement visible ;
- pas d'extension importante ni de garage formant un second volume ;
- ouvertures principales visibles ;
- idéalement une façade dont la largeur réelle est connue ou facilement mesurable.

Une maison plus complexe sera utile ensuite, mais pas pour valider le premier parcours.

## 2. Photos recommandées

Prendre idéalement 4 vues :
1. façade avant, assez droite et complète ;
2. côté gauche en montrant aussi un peu de l'avant ;
3. côté droit en montrant aussi un peu de l'avant ;
4. arrière.

Éviter si possible : très grand-angle, zoom numérique fort, végétation masquant toute une façade, photo coupant le toit ou le sol, et mélange de photos de dates différentes après travaux.

Si une façade est inaccessible, l'utilisateur doit pouvoir le dire dans les notes ; BrickHouse devra alors marquer cette partie comme inférée plutôt que comme observée.

## 3. Mesure de référence

Pour le premier essai, fournir si possible **la largeur réelle de la façade avant en mètres**. C'est l'ancre d'échelle prioritaire du MVP.

Le test reste possible sans mesure, mais l'évaluation des proportions absolues sera alors moins forte et BrickHouse doit l'indiquer explicitement.

## 4. Critères à vérifier dans le BuildingModel

Avant de construire les briques, vérifier :
- nombre de volumes ;
- largeur, profondeur et hauteur générale ;
- nombre de niveaux ;
- direction et pente approximative du toit ;
- nombre et répartition des portes/fenêtres sur chaque façade ;
- distinction observed / user_provided / inferred ;
- hypothèses et questions réellement utiles ;
- compatibilité M0 (`buildable`, blockers, warnings).

On ne juge pas encore la précision au centimètre. On cherche une représentation architecturale cohérente et honnête.

## 5. Critères à vérifier après génération LEGO

Dans le viewer :
- silhouette générale reconnaissable ;
- proportions largeur/profondeur/hauteur cohérentes ;
- toit dans le bon sens ;
- pignons/toiture sans gros trous structurels ;
- ouvertures principales au bon endroit ;
- aucune pièce visuelle absente du BrickModel/BOM.

Dans la BOM :
- total cohérent avec BrickModel ;
- fenêtres réelles uniquement lorsqu'une famille validée convient ;
- pas de référence inconnue créée pour embellir le rendu.

Dans la notice :
- toutes les pièces du modèle apparaissent exactement une fois dans le plan ;
- phases Structure / Fenêtres / Façades / Toiture ;
- étapes suffisamment courtes ;
- sous-assemblages de fenêtres compréhensibles.

## 6. Résultat du test

Noter chaque écart dans l'une des catégories suivantes :
- VISION : mauvaise compréhension des photos ;
- ÉCHELLE : dimensions/proportions métriques ;
- BUILDING MODEL : représentation ou validation architecturale ;
- LEGO ENGINE : conversion vers briques ;
- VIEWER : rendu seulement ;
- NOTICE : ordre/lisibilité du montage.

Cette classification est importante : elle évite de corriger le viewer pour masquer une erreur venant de la vision, ou de modifier la vision pour compenser un défaut du moteur LEGO.

## 7. Condition de passage à la maison suivante

On passe à une deuxième maison lorsque le premier cas simple arrive de bout en bout au viewer, à la BOM et à la notice, avec une silhouette et des ouvertures principales raisonnablement fidèles et sans simplification architecturale silencieuse.
