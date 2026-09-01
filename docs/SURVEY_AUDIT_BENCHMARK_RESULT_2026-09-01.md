# SurveyAudit benchmark — résultat du 2026-09-01

## Statut

**GO candidat pour une boucle de correction expérimentale contrôlée, avec benchmark formel encore incomplet.**

Cette conclusion autorise à tester le workflow explicite `SurveyAudit -> SurveyCorrection -> validation -> ré-audit ciblé`. Elle ne généralise pas encore SurveyAudit à toutes les maisons et ne justifie pas SceneAudit.

## Artefacts de mesure

Le benchmark utilise la maison réelle à 5 photos et le Survey `brickhouse-survey` produit depuis le handoff Photos -> Survey. La seule mesure utilisateur explicite du handoff est la largeur avant de 10 m.

Les photos, le PDF source et le Survey utilisateur restent privés et ne sont pas copiés dans le dépôt. Le dépôt conserve seulement ce compte rendu agrégé et les contrats génériques.

Prompt auditeur : `frontend/brickhouse-survey-independent-audit-v01.txt`.

Boundary désormais disponible : `POST /api/v1/validate-survey-audit`.

## Runs indépendants

Trois conversations indépendantes ont reçu le même PDF/photos, le même Survey intact et le même contrat SurveyAudit v0.1.

| Run | Findings | summary.status |
| --- | ---: | --- |
| 1 | 4 | `needs_correction` |
| 2 | 3 | `needs_correction` |
| 3 | 6 | `needs_correction` |
| **Total** | **13** | **3/3 needs_correction** |

Les réponses ont été conservées textuellement dans la session de benchmark, sans correction manuelle de leur JSON. Elles n'ont toutefois pas été déposées comme artefacts bruts persistants dans le repository.

## Adjudication visuelle

Sur les 13 findings :

- **12** sont jugés visuellement soutenus et utiles ;
- **1** est jugé faux positif : le Run 2 conteste l'identité de la fenêtre haute visible dans les photos 4 et 5 en affirmant que les vues montrent des faces différentes ; les repères visuels disponibles soutiennent plutôt l'identité déjà portée par le Survey ;
- **0** doublon intra-run a été retenu.

Convergences les plus fortes :

1. **toiture visible mais absente du Survey** : 3/3 runs ;
2. **relation `platform-support-relation` non soutenue dans son sens `platform supports building-envelope`** : 3/3 runs ; les images soutiennent un raccordement au bâtiment et une terrasse portée par sa propre structure, pas une terrasse supportant l'enveloppe bâtie.

Autres findings visuellement utiles apparus dans un seul run ou avec formulation différente : ouvertures visibles omises côté terrasse, seconde ouverture basse côté droit, calibration de certitude de l'association de cheminée au bâtiment cible, terrain visible côté gauche.

## Métriques établies

Les métriques suivantes ont un dénominateur observable dans les trois sorties :

| Mesure | Valeur | Note |
| --- | ---: | --- |
| findings totaux | 13 | 4 + 3 + 6 |
| findings soutenus | 12 | adjudication visuelle |
| faux positifs | 1 | identité fenêtre photos 4/5 |
| précision des findings | 0,923 | 12 / 13 |
| `actionable_precision` | 0,923 | 12 / 13 sur les findings déclenchant une action/revue utile |
| `evidence_precision` | 0,923 | une chaîne preuve -> conclusion a été rejetée avec le faux positif |
| `duplicate_rate` | 0,000 | aucun doublon intra-run retenu |
| `correction_trigger_rate` | 1,000 | 3 / 3 runs `needs_correction` |
| accord de statut | 1,000 | 3 / 3 |
| `net_new_true_findings` minimal démontré | >= 2 | toiture omise + relation de support visuellement non fondée, hors décision possible du JSON seul |

Le seuil expérimental de précision (`>= 0,80`), le seuil de précision de preuve (`>= 0,90`), le plafond de doublons (`<= 0,15`) et le minimum de deux findings visuels nouveaux sont donc franchis sur ce benchmark.

## Métriques non encore formellement établies

`recall`, F1, `identity_recall`, `omission_recall` et `certainty_precision` ne sont **pas** publiés comme scores définitifs ici. Leur calcul honnête exige une annotation gold exhaustive de toutes les anomalies actionnables de la maison, indépendante des sorties des auditeurs. Utiliser les seuls findings produits comme dénominateur créerait un rappel artificiellement élevé.

Le Jaccard complet des anomalies exige également une normalisation/adjudication persistée des identités de findings entre runs. La stabilité qualitative est néanmoins suffisante pour constater que les deux anomalies principales sont retrouvées 3/3 fois, alors que plusieurs omissions secondaires restent variables.

## Validation de contrat : limite du run historique

Les trois JSON ont été revus contre le contrat SurveyAudit v0.1 et leur structure apparente est cohérente : `survey_id`, `issue_count`, statuts, actions et références photo sont compatibles avec le Survey fourni.

Cependant, le boundary HTTP `POST /api/v1/validate-survey-audit` a été ajouté **après** la collecte de ces trois réponses, et les trois sorties brutes n'ont pas été persistées comme fichiers puis rejouées byte-for-byte contre ce boundary. Il serait donc incorrect d'affirmer que le critère « tous les runs machine-valides » est formellement clos pour cette collecte historique.

Un prochain benchmark formel devra sauvegarder les sorties brutes immédiatement, les valider sans retouche via le boundary, et conserver le résultat du validateur.

## Décision

### SurveyAudit

**GO candidat / expérimentation contrôlée.**

La valeur non redondante est démontrée qualitativement et dépasse les seuils de précision mesurables. La prochaine expérimentation doit utiliser `SurveyCorrection v0.1` comme artefact séparé : aucune mutation silencieuse du Survey source, journal de changements obligatoire, vérités utilisateur gelées, validation déterministe du candidat puis ré-audit ciblé seulement si nécessaire.

Le passage de « GO candidat » à « GO benchmark formel » nécessite encore :

1. conservation des trois sorties brutes ou d'un nouveau triplet de runs ;
2. validation machine exacte de chaque SurveyAudit sans correction manuelle ;
3. annotation gold exhaustive permettant le rappel/F1 et les rappels par catégorie ;
4. mesure de la boucle de correction sur un candidat sans perte de vérité utilisateur.

### SceneAudit

**HOLD.** Aucun résultat de ce benchmark ne mesure un gain propre au-dessus de `validate-scene-against-survey`. SceneAudit ne doit pas être ajouté par symétrie avec SurveyAudit.

## Invariants à préserver

- le Survey source du benchmark reste inchangé ;
- les validateurs déterministes restent obligatoires avant audit et après correction ;
- aucune vérité `user_provided` ne peut être modifiée automatiquement ;
- un finding `review` ou `keep` ne doit pas muter directement le Survey ;
- une correction doit être liée à un finding validé et rester explicitement inspectable ;
- les photos privées ne doivent pas être ajoutées au dépôt sans décision explicite.
