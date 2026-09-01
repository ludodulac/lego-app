# SurveyAudit benchmark v0.1

Date : 2026-09-01

## But

Mesurer si `SurveyAudit v0.1` apporte une valeur visuelle indépendante réelle au-dessus de la validation déterministe existante, sans récompenser le volume de critiques ni autoriser une mutation silencieuse du Survey.

Le benchmark principal reste le jeu réel de 5 photos. La largeur avant connue (10 m) peut être fournie au producteur Survey selon le protocole existant, mais l'auditeur ne doit pas inventer de métriques supplémentaires.

## Unité d'évaluation

L'unité est un **finding atomique**. Chaque finding est rapproché d'une vérité de référence : `TP` (correct), `FP` (non soutenu/mal ciblé), `FN` (anomalie actionnable manquée), `DUP` (doublon), `NEI` (`insufficient_evidence` correctement utilisé).

## Taxonomie minimale

Annoter : `physical_identity`, `omission`, `false_positive`, `orientation_or_side`, `certainty_calibration`, `relation`, `cross_view_contradiction`, `non_actionable`.

## Mesures obligatoires

Publier les nombres bruts TP/FP/FN/DUP/total et calculer : précision, rappel, F1, `duplicate_rate`, `actionable_precision`, `evidence_precision`, `identity_recall`, `omission_recall`, `certainty_precision`, `deterministic_overlap_rate`, `net_new_true_findings` et `correction_trigger_rate`.

`net_new_true_findings` compte uniquement les TP actionnables que `validate-survey` ne pouvait pas détecter sans vision.

## Protocole

1. figer Survey + PDF/photos ;
2. exécuter `validate-survey` et conserver ses issues ;
3. lancer l'auditeur dans un nouveau contexte avec le prompt dédié, le PDF et le Survey seulement ;
4. valider le résultat SurveyAudit via le boundary backend prévu ;
5. si le contrat est invalide, compter un échec de contrat et ne pas corriger manuellement le JSON ;
6. scorer contre la vérité de référence ;
7. répéter au moins 3 runs indépendants ;
8. ne déclencher aucune correction Survey pendant cette mesure initiale.

## Stabilité

Reporter l'accord sur `summary.status`, le Jaccard des anomalies retrouvées, la variation précision/rappel et les findings uniques à un seul run. Une amélioration moyenne très instable reste non concluante.

## GO / HOLD pour la boucle de correction

GO expérimental seulement si :

- `actionable_precision >= 0.80` ;
- `evidence_precision >= 0.90` ;
- `duplicate_rate <= 0.15` ;
- au moins 2 `net_new_true_findings` hors portée du validateur déterministe ;
- aucune proposition ne modifie une vérité `user_provided` sans contradiction explicitement prouvée ;
- tous les runs retenus respectent le contrat SurveyAudit ;
- pas de bascule fréquente `pass ↔ needs_correction` sans différence de preuves.

Ces seuils autorisent une phase expérimentale contrôlée, pas une généralisation produit à partir d'une seule maison.

## SceneAudit

Reste HOLD tant qu'on n'a pas documenté les erreurs photo-géométrie qui subsistent après `validate-scene-against-survey`. Ne pas l'implémenter seulement parce que SurveyAudit fonctionne.

## Artefacts à conserver

Survey d'entrée inchangé, version/hash du prompt, modèle utilisé, SurveyAudit brut, résultat du validateur, table de scoring et notes d'adjudication. Ne jamais remplacer le Survey source par une version corrigée dans le benchmark.
