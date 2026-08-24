# Boldungo / BrickHouse — reprise immédiate de conversation

Date : 2026-08-24

> À lire **après `HANDOFF.md`**. `main` reste la source de vérité si ce document diverge.

## 1. Dépôt / benchmark / URL

- dépôt : `ludodulac/lego-app`
- branche de vérité : `main`
- interface photo : `https://ludodulac.github.io/lego-app/photo.html`
- benchmark principal : `frontend/benchmarks/real-house-5/`
- ne jamais demander à l'utilisateur de renvoyer les 5 photos : elles sont déjà dans le dépôt.

## 2. État réel du chantier fidélité 5 photos

Le premier vrai run complet `5 photos -> Survey -> Scene -> LEGO -> viewer` a traversé le pipeline mais a produit un résultat architecturalement mauvais : toit/pignon perdu, ouvertures mal conservées, encadrements absents ou détails vitrés inventés, terrasse/escalier incohérents.

Depuis ce run, les corrections génériques suivantes ont été mergées sur `main` :

- PR #115 : toiture certaine préservée Survey -> Scene ; un gable incomplet ne peut plus devenir silencieusement un bâtiment ouvert côté LEGO.
- PR #116 : une observation `opening` représente exactement une ouverture physique (`physical_object_count:1`) ; plus de groupes comme `front_openings`.
- PR #117 : conservation de l'ordre qualitatif horizontal/vertical certain des ouvertures sans inventer de métrique.
- PR #118 : conservation des appuis/encadrements observés ; suppression du cadre de porte vitrée inventé à partir de texte libre.
- PR #119 : une terrasse/volée certaine corroborée multi-vues ne peut plus disparaître simplement parce que sa continuation cachée est inconnue.
- PR #120 : `ArchitecturalScene` peut conserver des relations topologiques avec `geometry_status:"resolved|unresolved"`; une relation `unresolved` conserve la compréhension physique mais bloque volontairement la projection LEGO.
- PR #121 : prompt Survey -> Scene v3.3 aligné sur ce contrat : topologie certaine != raccord métrique certain ; ne pas étirer/snaper une structure pour fermer une connexion cachée.
- PR #122 : correction du handoff PDF externe après un vrai échec d'import ; le PDF exige maintenant un `ArchitecturalSurvey` complet et une `ArchitecturalScene` complète, et interdit de mettre la topologie intermédiaire directement dans `survey`/`scene`.

## 3. Dernier test utilisateur et dernier bug observé

Le dernier fichier `brickhouse-external-result.json` produit par l'IA externe a été refusé à l'import avec :

`id : Field required · name : Field required · photos : Field required · relations.0.id : Field required · relations.0.kind : Field required · relations.0.statement : Field required ...`

Diagnostic confirmé : l'IA avait placé une structure de type topologie intermédiaire dans `survey` au lieu d'un `ArchitecturalSurvey v0.1` complet. Le backend a correctement refusé le fichier. Ne pas assouplir le backend pour accepter ce résultat.

PR #122 corrige précisément cette ambiguïté dans `frontend/brickhouse-single-package.js` et ajoute un test de non-régression. CI PR #122 verte, puis merge sur `main` au commit `1a7770c91bd8020d6c02eeced67a772cec0e71ee`.

## 4. Point exact de reprise

Avant de demander un nouveau run utilisateur :

1. vérifier que GitHub Pages a réellement redéployé le `main` contenant PR #122 ;
2. vérifier si possible que le fichier servi `brickhouse-single-package.js` contient la règle : `survey et scene ne sont PAS des résumés de la topologie` ;
3. si le connecteur ne permet pas d'inspecter directement l'environnement Pages, ne pas prétendre que le déploiement est confirmé ; utiliser le mécanisme GitHub disponible ou demander seulement le test minimal permettant de le constater ;
4. ensuite seulement demander à l'utilisateur de régénérer un **nouveau** `BRICKHOUSE-ANALYSE-COMPLETE.pdf` depuis `https://ludodulac.github.io/lego-app/photo.html` avec les 5 photos benchmark ;
5. nouveau chat IA vierge, joindre uniquement le nouveau PDF, récupérer le nouveau `brickhouse-external-result.json` sans correction manuelle ;
6. réimporter dans Boldungo et relever le premier refus ou, s'il passe, pousser jusqu'au viewer.

Ne jamais réutiliser l'ancien PDF ni l'ancien JSON après PR #122.

## 5. Objectif produit immédiat

Le but n'est plus d'ajouter des couches théoriques. Le prochain run réel doit valider que les garde-fous accumulés produisent effectivement un meilleur résultat avec les mêmes 5 photos.

Lors de ce run, observer en priorité :

- toiture/pignon conservé ou blocage honnête si métrique insuffisante ;
- inventaire exact des ouvertures et leur ordre ;
- encadrements observés présents, aucun vitrage décoratif inventé ;
- terrasse bois / dalle ou palier béton / escalier distingués seulement si les photos le soutiennent ;
- relations topologiques conservées même si un raccord caché reste `unresolved` ;
- aucune géométrie cachée inventée pour rendre le modèle constructible.

Si un `unresolved` bloque LEGO, ce n'est pas automatiquement un échec : vérifier d'abord si la compréhension architecturale est correcte et si le raccord est réellement non prouvé par les 5 vues.

## 6. Discipline de travail

- corriger la première cause réelle observée, pas le JSON du benchmark à la main ;
- correction générique + test de non-régression + CI verte + merge avant nouveau test utilisateur ;
- ne pas lancer de refonte parallèle sans lien direct avec le prochain test réel ;
- ne pas considérer `schema_valid` ou `constructible` comme synonyme de fidélité architecturale ;
- les photos supplémentaires de la maison servent seulement de vérité de contrôle, jamais à rendre artificiellement le benchmark 5 photos parfait ;
- main est toujours prioritaire sur cette passation.
