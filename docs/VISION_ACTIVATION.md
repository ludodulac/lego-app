# BrickHouse — activation contrôlée de l'analyse photo

L'analyse photo est volontairement séparée du moteur LEGO. Tant qu'aucune clé de fournisseur de vision n'est configurée, `/build`, le configurateur, le viewer, la BOM et la notice restent utilisables sans analyse IA.

## État désactivé attendu

`GET /api/v1/capabilities` doit renvoyer :
- `engine_ready: true` ;
- `photo_analysis_ready: false` ;
- `photo_provider: null` ;
- `photo_model: null` ;
- `photo_analysis_reason: "missing_server_api_key"`.

`GET /health` expose également `vision_enabled`, `vision_model` et `engine_revision`. Ces champs ne contiennent aucun secret.

Dans cet état, la page Photo doit désactiver le bouton d'analyse et ne doit envoyer aucune image.

## Préparation Render

`render.yaml` déclare uniquement le **nom** `OPENAI_API_KEY` avec `sync: false`. Cela permet à Render de gérer sa valeur comme un secret saisi dans le dashboard et non synchronisé depuis GitHub. La valeur de la clé ne doit jamais apparaître dans le dépôt.

`OPENAI_VISION_MODEL` reste une variable non secrète séparée. Cela permet de changer le modèle d'analyse sans toucher à la clé.

## Activation pour le premier essai réel

L'activation est une action volontaire et distincte du déploiement du moteur gratuit :
1. dans Render, ouvrir le service `brickhouse-api` puis ses variables d'environnement ;
2. saisir la valeur de `OPENAI_API_KEY` uniquement dans Render ;
3. vérifier la valeur souhaitée de `OPENAI_VISION_MODEL` ;
4. redéployer le service ;
5. ouvrir `/api/v1/capabilities` ;
6. ne poursuivre que si `photo_analysis_ready` vaut `true`, `photo_provider` vaut `openai`, et `photo_model` correspond au modèle attendu ;
7. effectuer d'abord un seul essai avec la maison simple définie dans `PHOTO_TRIAL_PROTOCOL.md`.

Important : l'activation d'une API de vision externe peut entraîner des coûts propres à ce fournisseur. Elle ne doit donc pas être faite automatiquement par le Blueprint ni confondue avec l'abonnement ChatGPT. Le logiciel reste utilisable sans cette activation pour toutes les fonctions qui ne nécessitent pas l'analyse photo.

## Secret : règle absolue

La **valeur** de la clé ne doit jamais être placée dans GitHub, dans `render.yaml`, dans le frontend, dans localStorage, dans une capture d'écran ou dans un fichier d'exemple. Seul son nom de variable est déclaré dans le Blueprint.

## Retour arrière

Pour désactiver immédiatement la vision, supprimer/vider `OPENAI_API_KEY` dans Render puis redéployer. Le moteur LEGO reste disponible.

## Critère de réussite avant essais supplémentaires

Ne pas multiplier les appels de vision tant que le premier essai n'a pas été classé selon les catégories VISION / ÉCHELLE / BUILDING MODEL / LEGO ENGINE / VIEWER / NOTICE. L'objectif est de corriger la bonne couche avant de consommer d'autres analyses.
