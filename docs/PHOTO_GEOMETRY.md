# BrickHouse — géométrie photo, perspective et proportions

Ce document fixe les règles du pipeline photo. L'objectif n'est pas de lire des distances brutes en pixels, mais de reconstruire une géométrie architecturale cohérente à partir de plusieurs vues en perspective.

## Principe

Une photographie en biais déforme les longueurs apparentes : les lignes parallèles convergent, les objets proches paraissent plus grands et les dimensions verticales prises depuis le sol sont raccourcies. BrickHouse doit donc travailler d'abord en **rapports géométriques sur une même façade**, puis convertir ces rapports en mètres seulement lorsqu'une échelle fiable est disponible.

## Contraintes à exploiter

Pour chaque façade, l'analyse doit raisonner sur la séquence : bord du mur -> ouverture -> espace -> ouverture -> bord opposé. Verticalement : sol -> appui -> fenêtre -> linteau -> égout de toit -> faîtage. Les coins, rangées de fenêtres, corniches, égouts et faîtages servent d'alignements. Des ouvertures répétées peuvent fournir des contraintes supplémentaires sans supposer automatiquement la symétrie.

Une vue presque frontale est privilégiée pour les positions horizontales sur une façade. Les vues obliques sont utiles pour la profondeur, les coins et la relation entre deux façades. Les dimensions importantes doivent être recoupées entre plusieurs vues quand elles existent.

## Échelle

Si une largeur réelle de façade est fournie, elle constitue l'ancre principale. BrickHouse doit d'abord retrouver les proportions normalisées, puis appliquer cette largeur à tout le système. Il ne faut jamais recalibrer indépendamment chaque fenêtre ou chaque espace.

Sans mesure connue, le BuildingModel peut utiliser une échelle métrique provisoire, mais `scale_basis` doit l'expliquer et la confiance doit être réduite. Une question doit demander une mesure réelle lorsque l'erreur d'échelle pourrait modifier sensiblement la maquette.

## Incertitude

Une zone masquée, recadrée, photographiée avec une très forte perspective ou incohérente entre plusieurs vues ne doit pas être inventée. Elle doit produire une preuve `uncertain`, une confiance plus faible et, si nécessaire, une question de clarification.

## Validation lors des essais

Pour les premiers essais réels, comparer séparément : largeur/profondeur globale, position normalisée des ouvertures, hauteur des appuis et linteaux, distance ouvertures-toiture, hauteur d'égout, hauteur de faîtage et pente apparente du toit. Une bonne reconstruction doit préserver ces rapports même si l'échelle absolue est encore provisoire.
