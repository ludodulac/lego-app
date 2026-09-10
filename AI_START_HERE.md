# AI START HERE — Boldüngo / BrickHouse

## Contexte transversal — obligatoire en nouvelle conversation

Ce projet appartient à l'écosystème documenté dans le dépôt GitHub **`ludodulac/Grand-pere`**. Grand Père est documenté dans le dépôt `ludodulac/Grand-pere`.

Au début d'une nouvelle conversation ou lorsqu'aucun contexte transversal fiable n'est déjà chargé :
1. ouvrir `ludodulac/Grand-pere` sur `main` ;
2. lire son `AI_START_HERE.md` ;
3. lire la fiche Boldüngo indiquée par `projects/_INDEX.md` ;
4. pour un travail itératif/autonome, appliquer `LOOP_ENGINEERING.md` ;
5. revenir ensuite dans **ce dépôt** et suivre le présent fichier.

**Le dépôt `ludodulac/lego-app` reste la source de vérité de l'état courant de Boldüngo. Grand Père fournit mémoire transversale, routage et méthode ; il ne remplace jamais code, données, tests, CI ou contrats locaux.**

Ce fichier est le point d’entrée obligatoire de tout agent IA qui reprend ce dépôt. Il ne décrit volontairement pas l’état technique du jour : il explique comment le reconstruire depuis les sources réelles et comment reprendre sans repartir de zéro.

## PROMPT OFFICIEL À COPIER DANS UNE NOUVELLE CONVERSATION

> Va dans le dépôt `ludodulac/lego-app`.
> Lis `AI_START_HERE.md` et suis exactement sa procédure de reprise, y compris le contexte transversal `ludodulac/Grand-pere`.
> Vérifie l’état réel de `main`, des PR/issues et de la CI avant d’agir.
> Reprends ensuite le chantier prioritaire indiqué par le dépôt.
> Ne repars pas de zéro et préserve l’existant.

Compatibilité historique : `Lis AI_START_HERE.md, vérifie l’état réel de main et reprends le projet.` reste une instruction courte valide.

## 1. Reprise rapide opérationnelle

Avant de lire largement le dépôt, reconstruire seulement ce qui est nécessaire pour agir :

1. **État réel** — lire le HEAD de `main`, les PR ouvertes et les derniers checks/CI pertinents.
2. **Priorité** — lire la section de reprise de `PROGRESSION.md`, puis confirmer le chantier dans les PR/issues et le code actuels.
3. **Zone** — identifier la frontière du pipeline touchée et utiliser `docs/_INDEX.md` pour router la lecture.
4. **Garde-fous** — relire les invariants concernés dans `PROJECT_PRINCIPLES.md` et les contrats spécialisés.
5. **Validation** — FAST pendant l'itération, TARGETED pour la couche et ses frontières, FULL avant fusion ou lorsque le risque traverse plusieurs couches.
6. **Terminé** — modification minimale, preuve proportionnée, régression si bug, CI lorsque requise, puis décision explicite CONTINUE / PIVOT / STOP selon `LOOP_ENGINEERING.md`.

### Invariants sentinelles

- **Survey = autorité sémantique.** Une transformation aval ne réécrit pas silencieusement objets, identités, relations ou certitudes observées.
- **Scene = autorité métrique/géométrique.** La génération LEGO peut approximer sa représentation, pas muter la Scene pour rendre le modèle constructible.
- **Un inconnu reste inconnu.** Pas de mesure, coordonnée, pente, support, objet ou certitude inventé pour faire passer un pipeline.
- **Les pertes restent explicites.** Approximation, simplification et impossibilité de fidélité se propagent via diagnostics/provenance au lieu d'être masquées.
- **Support physique ≠ proximité visuelle.** Une garantie de production exige une preuve dans le périmètre déclaré.
- **Artefacts aval cohérents.** BOM, AssemblyPlan, InstructionPlan et BagPlan ne revendiquent pas plus que leurs validateurs ne prouvent.
- **Préserver avant de remplacer.** Une optimisation ne supprime aucune capacité métier existante et une correction vise la cause générique.

## 2. Sources de vérité

- Constitution : `PROJECT_PRINCIPLES.md`.
- Vision/pipeline : `README.md`.
- Progression et reprise : `PROGRESSION.md`.
- Routage documentaire : `docs/_INDEX.md`.
- Survey / Scene / raisonnement photo : contrats spécialisés dans `docs/`.
- Comportement garanti : code + tests.
- État technique courant : GitHub + `main` réel + CI/déploiement.
- Méthode transversale : Grand Père `LOOP_ENGINEERING.md`, subordonnée aux vérités locales ci-dessus.

## 3. Règles de travail

- Traiter le dépôt comme un logiciel existant, jamais comme un projet vierge.
- Préserver l'existant : ajouter/étendre avant de remplacer ou supprimer.
- Distinguer objectif utilisateur et ancienne solution technique.
- Ne jamais inventer géométrie, mesure ou certitude.
- Corriger la première frontière du pipeline où l'information devient fausse ou disparaît.
- Vérifier le chemin réellement déployé lorsque la fonctionnalité dépend du frontend ou d'un pipeline différent des tests unitaires.
- Ne solliciter l'utilisateur que pour une vraie décision humaine ; continuer autonomement tant que des boucles bornées produisent une preuve utile.
- Une autonomie longue doit être composée de petites boucles observables, pas d'une commande opaque interminable.

## 4. Passation

Une information importante ne doit pas rester uniquement dans une conversation. Mettre les règles durables dans leur source canonique, la progression opérationnelle dans `PROGRESSION.md`, les décisions d'architecture dans la documentation appropriée et les régressions reproductibles dans les tests.

Avant de terminer une tranche substantielle, laisser au minimum : **objectif / dernière boucle / preuve / état courant / prochaine décision**.

Test final : une nouvelle conversation doit pouvoir partir de ce fichier, découvrir Grand Père, revenir au vrai `main`, identifier la priorité et reprendre sans demander à l'utilisateur de raconter l'historique.
