# BrickHouse — activation contrôlée de l'analyse photo

L'analyse photo est volontairement séparée du moteur LEGO. Tant qu'aucune clé de fournisseur de vision n'est configurée, `/build`, le configurateur, le viewer, la BOM et la notice restent utilisables sans analyse IA.

## État désactivé attendu

`GET /api/v1/capabilities` doit renvoyer :
- `engine_ready: true` ;
- `photo_analysis_ready: false` ;
- `photo_provider: null`.

Dans cet état, la page Photo doit désactiver le bouton d'analyse et ne doit envoyer aucune image.

## Activation pour le premier essai réel

Quand on décide explicitement de faire le premier essai avec un fournisseur réel :
1. ajouter `OPENAI_API_KEY` comme variable d'environnement secrète du service `brickhouse-api` dans Render ;
2. conserver `OPENAI_VISION_MODEL` comme variable séparée pour pouvoir changer de modèle sans toucher au code ;
3. redéployer le service ;
4. vérifier `/api/v1/capabilities` avant d'envoyer une photo ;
5. n'effectuer d'abord qu'un seul essai avec la maison simple définie dans `PHOTO_TRIAL_PROTOCOL.md`.

La clé ne doit jamais être placée dans GitHub, dans `render.yaml`, dans le frontend, dans localStorage ou dans un fichier d'exemple.

## Retour arrière

Pour désactiver immédiatement la vision, supprimer/vider `OPENAI_API_KEY` dans Render puis redéployer. Le moteur LEGO reste disponible.

## Critère de réussite avant essais supplémentaires

Ne pas multiplier les appels de vision tant que le premier essai n'a pas été classé selon les catégories VISION / ÉCHELLE / BUILDING MODEL / LEGO ENGINE / VIEWER / NOTICE. L'objectif est de corriger la bonne couche avant de consommer d'autres analyses.
