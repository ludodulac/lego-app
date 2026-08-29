# Boldüngo — contrat manuel ChatGPT avant API

Date de référence : 2026-08-29

Ce document décrit le **flux manuel actuellement actif** entre Boldüngo et ChatGPT. Il constitue le contrat produit à stabiliser avant de remplacer les échanges manuels par une API IA.

## Principe

Le flux est volontairement séparé en deux étapes afin que Boldüngo valide la compréhension sémantique de la maison avant de demander une reconstruction géométrique.

Les photos doivent être réellement accessibles au modèle. Un chemin de fichier local, un nom de photo ou un résumé textuel ne remplace jamais les pixels.

Le flux legacy `external-bundle-0.1` reste accepté par l'importeur pour compatibilité, mais il n'est plus le parcours principal.

## Étape A — photos vers ArchitecturalSurvey

### Entrée générée par Boldüngo

Depuis `frontend/photo.html`, Boldüngo crée :

`BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf`

Le générateur actif est `frontend/brickhouse-survey-package-v04.js`, chargé par `frontend/brickhouse-survey-package.js`.

Le PDF contient :

- la commande de handoff ;
- les règles d'autorité d'orientation ;
- les faits fournis par l'utilisateur ;
- les prompts de topologie et d'ArchitecturalSurvey ;
- les **photos sélectionnées elles-mêmes**, rendues comme pages du PDF.

Les quatre groupes de façade sont `front`, `right`, `left`, `rear`. Les groupes de détail sont `detail_1` à `detail_6` et n'ont aucune façade implicite.

### Sortie exigée de ChatGPT

Nom exact :

`brickhouse-survey-result.json`

Le fichier contient directement un objet **ArchitecturalSurvey v0.1** à la racine :

- `schema_version` vaut `0.1` ;
- aucun wrapper `survey` ;
- aucune ArchitecturalScene ;
- aucune topologie intermédiaire à la racine.

La topologie sert uniquement au raisonnement de l'étape IA ; elle ne remplace jamais le contrat Survey.

### Validation Boldüngo

Boldüngo envoie le Survey à :

`POST /api/v1/validate-survey`

La suite n'est autorisée que lorsque la réponse indique `valid_for_scene_fusion = true`.

Le Survey validé devient la source de vérité sémantique : inventaire d'objets, IDs, certitudes, relations et mesures utilisateur connues.

## Étape B — Survey validé + photos vers ArchitecturalScene

### Entrées générées / conservées par Boldüngo

Boldüngo crée :

`BRICKHOUSE-SURVEY-TO-SCENE.txt`

Version active du contrat photo :

`scene-handoff-0.4-photo-evidence`

À cette étape, l'utilisateur doit fournir dans la **même conversation ChatGPT** :

1. `BRICKHOUSE-SURVEY-TO-SCENE.txt` ;
2. le PDF photo original `BRICKHOUSE-SURVEY-pdf-handoff-0.4.pdf`.

Le Survey inclus dans le TXT reste autoritatif pour les objets et relations. Le PDF sert seulement de preuve visuelle complémentaire pour contraindre la géométrie : profondeur, hauteur, dimensions secondaires, pente, visibilité et raccords physiques.

Si le PDF photo n'est pas réellement accessible, aucune métrique manquante ne doit être inventée pour rendre la Scene complète.

### Sortie exigée de ChatGPT

Nom exact :

`brickhouse-scene-result.json`

Le fichier contient directement un objet **ArchitecturalScene v0.2** à la racine :

- `schema_version` vaut `0.2` ;
- aucun wrapper `scene` ;
- aucun Survey recopié ;
- aucune enveloppe `external-bundle`.

### Validation Boldüngo

Boldüngo contrôle d'abord la fidélité au Survey :

`POST /api/v1/validate-scene-against-survey`

Puis la validité géométrique de la Scene :

`POST /api/v1/validate-scene`

La construction n'est proposée qu'après ces contrôles.

## Autorités et incertitudes

Ordre de priorité :

1. fait explicite fourni par l'utilisateur ;
2. fait certain validé dans l'ArchitecturalSurvey ;
3. géométrie déduite de preuves multi-vues ;
4. estimation explicitement marquée avec sa provenance ;
5. inconnu conservé comme inconnu.

Une sortie IA n'a pas le droit de compléter une zone cachée uniquement parce qu'une architecture « typique » serait plausible.

## Questions supplémentaires

La cible produit est zéro à deux échanges supplémentaires après les deux handoffs principaux. Une question supplémentaire n'est justifiée que si sa réponse réduit matériellement une ambiguïté architecturale qui bloque ou dégrade fortement la maquette.

Si une vue précise peut être reprise, Boldüngo peut demander cette vue. Si elle ne peut pas être obtenue, le pipeline doit continuer avec l'incertitude explicite lorsque c'est constructible sans invention.

## Compatibilité legacy

`frontend/external-bundle-import.js` accepte encore :

- `schema_version: external-bundle-0.1` ;
- `kind: brickhouse_external_result` ;
- `survey` v0.1 ;
- `scene` v0.2.

Cette enveloppe est une compatibilité historique. Elle ne doit pas redevenir le contrat principal ni forcer le parcours actif à reconstruire Survey et Scene en un seul tour.

## Critères avant automatisation API

Le passage à une API IA ne doit pas changer le contrat métier. Avant cette automatisation, plusieurs essais doivent démontrer que :

- les photos du package sont effectivement lisibles par le modèle ;
- un Survey retourné sans modification manuelle est validable ou échoue avec un diagnostic utile ;
- la Scene retournée sans modification manuelle est validable contre ce Survey ;
- les inconnues restent explicites ;
- aucun benchmark particulier n'est codé comme règle générale ;
- les mêmes contrats Survey v0.1 et Scene v0.2 restent utilisables par le backend ;
- les corrections portent sur la cause générique d'un échec, jamais sur un JSON benchmark édité à la main.
