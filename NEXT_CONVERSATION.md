# Boldüngo / BrickHouse — reprise immédiate

Date : 2026-08-31

## À lire dans cet ordre

1. `AI_START_HERE.md`
2. `README.md`
3. `docs/CURRENT_PROJECT_STATE.md`
4. `docs/ARCHITECTURE.md` et `docs/DECISIONS.md`
5. les contrats spécialisés concernés par la tâche
6. `HANDOFF.md` seulement pour l’historique de continuité utile

Toujours vérifier l’état réel de `main`, des PR/issues et de la CI/Pages avant d’agir. `main` et les tests exécutables priment sur cette passation.

## FAIT ET VÉRIFIÉ au point de passation

- La série de corrections #283 à #305 a été fusionnée jusqu’au commit `62655f6e1bd33c3ea469fe10af2ada27c586a889`.
- La CI de `main` et le déploiement GitHub Pages correspondants ont réussi.
- Le workflow photo principal est le handoff en deux étapes Photos → Survey puis Survey + PDF → Scene.
- Le Survey est l’autorité sémantique ; la Scene est l’autorité métrique/géométrique.
- Les contraintes LEGO ne doivent pas réécrire la vérité architecturale.
- Les audits Photos → Survey sont volontairement additifs : prompt historique + audit terrain v2.9 + audit topologique v3.0.
- Le moteur géométrique LEGO LDraw est intégré ; il valide collision/contact/connecteurs/supports dans son périmètre actuel.

Tous les détails, chemins de fichiers, limites et régressions sont indexés dans `docs/CURRENT_PROJECT_STATE.md`.

## OUVERT

- Issue #274 / BH-090 : validation humaine bout-en-bout du round-trip manuel.
- Avant de redemander un run humain, vérifier les trois drifts repérés dans le dernier Survey neutre : contrat `targeted_detail`, attribut qualitatif de toiture, vocabulaire qualitatif de pente terrain.
- Vérifier et supprimer toute mention documentaire/prompt encore obsolète de `terrain.facade_grade_profiles` ; le contrat Scene canonique est `terrain.profiles`.
- Après stabilisation sémantique, continuer la fidélité physique/visuelle : fenêtres, terrasse, escalier, terrain/rue/trottoir, position métrique prudente de la cheminée.

## PROCHAINE ÉTAPE

La prochaine conversation ne doit pas demander immédiatement à l’utilisateur de refaire le benchmark.

Elle doit d’abord :
1. vérifier `main`, PR/issues, CI et Pages ;
2. traiter les contradictions ou drifts de contrat encore vérifiables automatiquement ;
3. ajouter les régressions nécessaires ;
4. merger/déployer ;
5. seulement ensuite demander une unique nouvelle génération Photos → Survey avec les mêmes 5 photos et la largeur avant de 10 m ;
6. auditer le Survey intact avant de lancer Survey → Scene.

## À NE PAS REFAIRE

- ne pas modifier manuellement un JSON utilisateur pour le faire passer ;
- ne pas assouplir le backend pour accepter un pseudo-Survey ou une pseudo-Scene ;
- ne pas coder une règle propre à la maison benchmark ;
- ne pas réécrire/condense le prompt Survey historique en supprimant des garde-fous ;
- ne pas demander un test utilisateur après chaque petit correctif ;
- ne pas faire passer artificiellement un test reproductible qui échoue.

## Instruction suffisante pour repartir

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet.
