# BrickHouse — activation contrôlée de l'analyse photo

L'analyse photo est volontairement séparée du moteur LEGO. Le fournisseur est **toujours choisi explicitement** avec `BRICKHOUSE_VISION_PROVIDER`. La présence accidentelle d'une clé dans l'environnement ne suffit donc jamais à envoyer des photos.

## État désactivé attendu

Par défaut `BRICKHOUSE_VISION_PROVIDER=none`.

`GET /api/v1/capabilities` doit alors renvoyer :
- `engine_ready: true` ;
- `photo_analysis_ready: false` ;
- `photo_provider: null` ;
- `photo_model: null` ;
- `photo_analysis_reason: "provider_not_selected"`.

`GET /health` expose également `vision_enabled`, `vision_provider`, `vision_model`, `vision_reason` et `engine_revision`. Ces champs ne contiennent aucun secret.

Dans cet état, la page Photo désactive le bouton d'analyse et n'envoie aucune image.

## Fournisseurs préparés

### OpenAI
Variables Render :
- `BRICKHOUSE_VISION_PROVIDER=openai` ;
- valeur secrète `OPENAI_API_KEY` ;
- modèle dans `OPENAI_VISION_MODEL`.

L'API OpenAI est facturée séparément de ChatGPT. Il faut donc considérer ce choix comme une activation potentiellement payante.

### Google Gemini
Variables Render :
- `BRICKHOUSE_VISION_PROVIDER=gemini` ;
- valeur secrète `GEMINI_API_KEY` ;
- modèle dans `GEMINI_VISION_MODEL` (Blueprint : `gemini-3.6-flash`).

BrickHouse utilise pour le MVP l'entrée image inline et les sorties JSON structurées. Le fournisseur documente une limite totale inférieure à 20 Mo pour une requête inline ; BrickHouse applique volontairement une marge plus stricte de 14 Mo de photos brutes cumulées afin de laisser de la place au prompt et au schéma.

Le niveau gratuit Gemini peut être utile pour les premiers essais, mais ses conditions de traitement des données ne doivent pas être confondues avec celles d'une offre payante. Pour des photos de maison réelles, le choix du fournisseur reste donc une décision explicite de l'utilisateur.

## Secrets : règle absolue

`render.yaml` déclare uniquement les **noms** `OPENAI_API_KEY` et `GEMINI_API_KEY` avec `sync: false`. Les valeurs sont saisies uniquement dans Render.

La valeur d'une clé ne doit jamais être placée dans GitHub, le frontend, localStorage, une capture d'écran ou un fichier d'exemple.

## Activation du premier essai réel

1. choisir explicitement `openai` ou `gemini` ;
2. dans Render, ouvrir `brickhouse-api` puis ses variables d'environnement ;
3. saisir uniquement la clé correspondant au fournisseur choisi ;
4. régler `BRICKHOUSE_VISION_PROVIDER` sur ce fournisseur ;
5. vérifier le modèle associé ;
6. redéployer ;
7. ouvrir `/api/v1/capabilities` ;
8. ne poursuivre que si `photo_analysis_ready=true`, avec le fournisseur et le modèle attendus ;
9. faire un seul essai selon `PHOTO_TRIAL_PROTOCOL.md` et télécharger son rapport avant un deuxième appel.

## Retour arrière immédiat

Mettre `BRICKHOUSE_VISION_PROVIDER=none` puis redéployer. Aucune suppression de clé n'est nécessaire pour couper les appels ; le moteur LEGO reste disponible.

## Critère de réussite avant essais supplémentaires

Ne pas multiplier les appels de vision tant que le premier essai n'a pas été classé selon VISION / ÉCHELLE / BUILDING MODEL / LEGO ENGINE / VIEWER / NOTICE. L'objectif est de corriger la bonne couche avant de consommer d'autres analyses.
