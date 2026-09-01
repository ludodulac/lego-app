# Boldüngo / BrickHouse — reprise immédiate

Date : 2026-09-01

## À lire dans cet ordre

1. `AI_START_HERE.md`
2. `README.md`
3. `docs/CURRENT_PROJECT_STATE.md`
4. `docs/ARCHITECTURE.md` et `docs/DECISIONS.md`
5. les contrats spécialisés concernés par la tâche
6. `HANDOFF.md` seulement pour l’historique utile

Toujours vérifier l’état réel de `main`, des PR/issues, de la CI et de Pages avant d’agir. `main` et les tests exécutables priment sur cette passation.

## FAIT ET VÉRIFIÉ

- PR #308 : contrat sémantique de direction de pente terrain clarifié.
- PR #309 : audit de couverture Survey v3.1 ajouté (roof, building boundary, root `id`, etc.).
- PR #310 : cache-buster du package Survey corrigé.
- PR #311 : handoff Survey → Scene verrouillé sur le Survey actif validé ; l’état Survey/Scene obsolète est invalidé avant un nouvel import. Cause probable des Scenes incohérentes : un ancien Survey validé pouvait survivre en localStorage et alimenter le handoff.
- `main` après #311 : `4ad4307f2e4a8f47dc204a3d952c16d144a977ca`.
- CI post-merge #1281 : SUCCESS. Pages #519 : SUCCESS.
- Issue pipeline : #274 / BH-090.
- Issue UX : #312.

## DÉCISION PRODUIT DURABLE — INTERFACE UNIQUE

L'utilisateur a explicitement fixé l'invariant suivant : **Boldüngo doit être une application à UNE SEULE PAGE / UN SEUL ÉCRAN PRINCIPAL**, dans l'esprit d'efficacité mobile de Clash Royale, sans copier son identité graphique ni ses assets.

Le parcours normal ne doit pas devenir une succession `Photos → Survey → Scene → Maquette` de pages. Ce sont des **états du même shell applicatif** : navigation basse persistante, progression toujours visible, panneaux/cartes/tiroirs/modales/overlays, actions principales accessibles au pouce, faible profondeur et pas de long scroll pour le parcours principal. Les anciennes routes peuvent rester temporairement pour compatibilité pendant la migration.

La décision et les principes sont suivis dans #312 : `Single-screen mobile Boldüngo shell inspired by Clash Royale UX principles`.

## ÉTAT DU BENCHMARK

Le dernier Survey brut a révélé notamment qu'une observation `opening` pouvait regrouper plusieurs ouvertures physiques (`physical_object_count > 1`), ce que le backend refuse. Les garde-fous Photos → Survey ont été renforcés ; ne pas corriger le JSON utilisateur à la main.

Les dernières Scenes avaient notamment : terrain vide malgré des observations terrain actives, alias inventé pour `building_boundary`, perte d'informations roof et IDs ne correspondant pas au Survey. #311 traite la cause de stale state/source mismatch avant de conclure à un défaut du prompt Scene.

## PROCHAINE ACTION HUMAINE EN ATTENTE

L'utilisateur doit maintenant faire **une seule nouvelle génération Photos → Survey** depuis la version déployée : mêmes 5 photos benchmark, largeur réelle façade avant = 10 m, aucune note destinée à aider l'IA, nouvelle conversation IA neutre, puis fournir le `brickhouse-survey-result.json` BRUT **avant import dans Boldüngo**.

À réception : auditer le Survey intact (root `id`, largeur 10 m, une ouverture physique par observation, vocabulaire, building_boundary, roof, terrain, chimney si visible, platform/stair/volume secondaire, relations). Si invalide, chercher/corriger la cause générique avant de redemander un run humain. S'il est valide, guider l'import puis Survey → Scene, et auditer la Scene avant toute construction.

## TRAVAIL AUTONOME POSSIBLE EN ATTENDANT

Continuer la conception/migration additive du shell one-screen #312 sans casser le benchmark : auditer `index.html`, `photo.html`, CSS/JS/viewer, cartographier les hooks/états, documenter l'architecture UX et absorber progressivement le workflow dans un viewport mobile unique. La priorité de livraison reste cependant la fidélité du pipeline architectural.

## À NE PAS REFAIRE

- ne pas renommer mécaniquement BrickHouse en Boldüngo ;
- ne pas modifier un JSON utilisateur pour le faire passer ;
- ne pas affaiblir les validateurs ;
- ne pas hardcoder la maison benchmark ;
- ne pas demander à l'utilisateur du travail GitHub/technique réalisable par l'agent ;
- ne pas demander un test humain après chaque micro-correctif ;
- ne pas traiter « mobile-first » comme une simple longue page responsive : la cible est réellement un **shell principal unique**.

## Instruction suffisante pour repartir

> Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet.
