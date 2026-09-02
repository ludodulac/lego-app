# SurveyAudit formal benchmark — aggregate result

Date: 2026-09-02

## Privacy boundary

The source PDF/photos, ArchitecturalSurvey payload, raw SurveyAudit JSON bodies, exhaustive visual gold notes, and correction candidate remain outside the repository. This file records only non-private aggregate benchmark state.

## Formal triplet replay

Three fresh independent SurveyAudit runs were produced with `frontend/brickhouse-survey-independent-audit-v01.txt` unchanged and the same frozen private PDF + Survey inputs.

Replay against the current `SurveyAudit v0.1` contract and semantic boundary:

| run | findings | audit status | contract/boundary |
| --- | ---: | --- | --- |
| formal-1 | 5 | `needs_correction` | valid |
| formal-2 | 4 | `needs_correction` | valid |
| formal-3 | 5 | `needs_correction` | valid |

No raw audit was edited, normalized, deduplicated, or repaired before replay.

## Exhaustive gold + scorecard

An exhaustive gold annotation was built separately from the retained runs using the frozen private Survey and source photos. The private scorecard contains 7 gold anomalies and accounts for every anomaly as detected or missed in every retained run.

Aggregate executable-scorecard-equivalent metrics:

| metric | result |
| --- | ---: |
| total findings | 14 |
| TP | 13 |
| FP | 1 |
| FN | 8 |
| DUP | 0 |
| NEI | 0 |
| precision | 0.9286 |
| recall | 0.6190 |
| F1 | 0.7429 |
| duplicate_rate | 0.0000 |
| actionable_precision | 0.9286 |
| evidence_precision | 0.9286 |
| identity_recall | 1.0000 |
| omission_recall | 0.5833 |
| certainty_precision | 0.0000 |
| deterministic_overlap_rate | 0.0000 |
| net_new_true_findings | 6 |
| correction_trigger_rate | 1.0000 |
| contract_valid_rate | 1.0000 |
| status_agreement | 1.0000 |
| anomaly_jaccard_mean | 0.6333 |
| precision_range | 0.2000 |
| recall_range | 0.1429 |
| single_run_true_findings | 2 |

No `user_provided` truth is changed by this benchmark and no unsupported `pass` / `needs_correction` status flip occurred.

## Decision

**GO experimental** for the bounded SurveyCorrection loop.

The explicit benchmark v0.1 GO blockers are all clear:

- actionable precision >= 0.80;
- evidence precision >= 0.90;
- duplicate rate <= 0.15;
- at least two net-new true findings beyond deterministic validation;
- all retained runs contract-valid;
- no unsupported user truth change;
- no unexplained status flip.

Recall/F1 remain reporting metrics, not GO thresholds in benchmark v0.1. The moderate recall and cross-run Jaccard are retained as stability cautions rather than silently treated as product-generalization evidence.

## Controlled continuation

Proceed only with automatically eligible `SurveyCorrection v0.1` findings. Prefer a conservative correction subset whose findings are visually adjudicated true and whose mutation shape does not require the manual-only `merge` or photo-level `reorient` surfaces. Validate the complete candidate, preserve all frozen/user-provided truth, then run the bounded `SurveyCorrectionReaudit` scope. `SceneAudit` remains HOLD.
