from __future__ import annotations

import pytest
from pydantic import ValidationError

from brickhouse.survey.benchmark import (
    SurveyAuditBenchmarkCategory,
    SurveyAuditBenchmarkRun,
    SurveyAuditBenchmarkScorecard,
    SurveyAuditFindingAdjudication,
    SurveyAuditGoldAnomaly,
    compute_survey_audit_benchmark_metrics,
    evaluate_survey_audit_experimental_go,
)


def _finding(
    finding_id: str,
    *,
    label: str = "TP",
    category: str = "omission",
    gold_anomaly_id: str | None = None,
    actionable: bool = True,
    evidence_supported: bool = True,
    deterministic_overlap: bool = False,
) -> SurveyAuditFindingAdjudication:
    return SurveyAuditFindingAdjudication.model_validate(
        {
            "finding_id": finding_id,
            "label": label,
            "category": category,
            "gold_anomaly_id": gold_anomaly_id,
            "actionable": actionable,
            "evidence_supported": evidence_supported,
            "deterministic_overlap": deterministic_overlap,
        }
    )


def _complete_scorecard() -> SurveyAuditBenchmarkScorecard:
    gold = [
        SurveyAuditGoldAnomaly(
            id="missing-roof",
            category=SurveyAuditBenchmarkCategory.OMISSION,
        ),
        SurveyAuditGoldAnomaly(
            id="unsupported-platform-support",
            category=SurveyAuditBenchmarkCategory.RELATION,
        ),
        SurveyAuditGoldAnomaly(
            id="upper-opening-identity",
            category=SurveyAuditBenchmarkCategory.PHYSICAL_IDENTITY,
        ),
    ]
    runs = [
        SurveyAuditBenchmarkRun(
            run_id="run-1",
            contract_valid=True,
            audit_status="needs_correction",
            findings=[
                _finding("r1-roof", gold_anomaly_id="missing-roof"),
                _finding(
                    "r1-relation",
                    category="relation",
                    gold_anomaly_id="unsupported-platform-support",
                ),
                _finding(
                    "r1-identity",
                    category="physical_identity",
                    gold_anomaly_id="upper-opening-identity",
                ),
            ],
        ),
        SurveyAuditBenchmarkRun(
            run_id="run-2",
            contract_valid=True,
            audit_status="needs_correction",
            findings=[
                _finding("r2-roof", gold_anomaly_id="missing-roof"),
                _finding(
                    "r2-relation",
                    category="relation",
                    gold_anomaly_id="unsupported-platform-support",
                ),
                _finding(
                    "r2-certainty-fp",
                    label="FP",
                    category="certainty_calibration",
                    evidence_supported=False,
                ),
            ],
            missed_gold_anomaly_ids=["upper-opening-identity"],
        ),
        SurveyAuditBenchmarkRun(
            run_id="run-3",
            contract_valid=True,
            audit_status="needs_correction",
            findings=[
                _finding("r3-roof", gold_anomaly_id="missing-roof"),
                _finding(
                    "r3-relation",
                    category="relation",
                    gold_anomaly_id="unsupported-platform-support",
                ),
                _finding(
                    "r3-identity",
                    category="physical_identity",
                    gold_anomaly_id="upper-opening-identity",
                ),
                _finding(
                    "r3-duplicate",
                    label="DUP",
                    category="omission",
                    gold_anomaly_id=None,
                ),
            ],
        ),
    ]
    return SurveyAuditBenchmarkScorecard(
        runs=runs,
        gold_set_complete=True,
        gold_anomalies=gold,
    )


def test_complete_scorecard_computes_required_metrics_and_stability() -> None:
    metrics = compute_survey_audit_benchmark_metrics(_complete_scorecard())

    assert metrics.total_findings == 10
    assert (metrics.tp, metrics.fp, metrics.fn, metrics.dup, metrics.nei) == (8, 1, 1, 1, 0)
    assert metrics.precision == pytest.approx(8 / 9)
    assert metrics.recall == pytest.approx(8 / 9)
    assert metrics.f1 == pytest.approx(8 / 9)
    assert metrics.duplicate_rate == pytest.approx(0.1)
    assert metrics.actionable_precision == pytest.approx(0.8)
    assert metrics.evidence_precision == pytest.approx(0.9)
    assert metrics.identity_recall == pytest.approx(2 / 3)
    assert metrics.omission_recall == pytest.approx(1.0)
    assert metrics.certainty_precision == pytest.approx(0.0)
    assert metrics.deterministic_overlap_rate == pytest.approx(0.0)
    assert metrics.net_new_true_findings == 3
    assert metrics.correction_trigger_rate == pytest.approx(1.0)
    assert metrics.contract_valid_rate == pytest.approx(1.0)
    assert metrics.status_agreement == pytest.approx(1.0)
    assert metrics.anomaly_jaccard_mean == pytest.approx(7 / 9)
    assert metrics.precision_range == pytest.approx(1 / 3)
    assert metrics.recall_range == pytest.approx(1 / 3)
    assert metrics.single_run_true_findings == 0


def test_complete_scorecard_meets_explicit_go_thresholds() -> None:
    decision = evaluate_survey_audit_experimental_go(_complete_scorecard())

    assert decision.go_experimental is True
    assert decision.blockers == []


def test_incomplete_gold_set_does_not_invent_recall_or_net_new_count() -> None:
    scorecard = SurveyAuditBenchmarkScorecard(
        runs=[
            SurveyAuditBenchmarkRun(
                run_id="run-1",
                contract_valid=True,
                audit_status="needs_correction",
                findings=[_finding("roof")],
            )
        ]
    )

    metrics = compute_survey_audit_benchmark_metrics(scorecard)
    decision = evaluate_survey_audit_experimental_go(scorecard)

    assert metrics.fn is None
    assert metrics.recall is None
    assert metrics.f1 is None
    assert metrics.identity_recall is None
    assert metrics.omission_recall is None
    assert metrics.net_new_true_findings is None
    assert decision.go_experimental is False
    assert "net_new_true_findings_not_reproducible" in decision.blockers


def test_complete_gold_set_requires_every_run_to_account_for_every_anomaly() -> None:
    with pytest.raises(ValidationError, match="detected or missed"):
        SurveyAuditBenchmarkScorecard(
            gold_set_complete=True,
            gold_anomalies=[
                SurveyAuditGoldAnomaly(
                    id="missing-roof",
                    category="omission",
                ),
                SurveyAuditGoldAnomaly(
                    id="bad-relation",
                    category="relation",
                ),
            ],
            runs=[
                SurveyAuditBenchmarkRun(
                    run_id="run-1",
                    contract_valid=True,
                    audit_status="needs_correction",
                    findings=[
                        _finding(
                            "roof",
                            gold_anomaly_id="missing-roof",
                        )
                    ],
                )
            ],
        )


def test_run_rejects_same_gold_anomaly_as_detected_and_missed() -> None:
    with pytest.raises(ValidationError, match="both detected and missed"):
        SurveyAuditBenchmarkRun(
            run_id="run-1",
            contract_valid=True,
            audit_status="needs_correction",
            findings=[_finding("roof", gold_anomaly_id="missing-roof")],
            missed_gold_anomaly_ids=["missing-roof"],
        )


def test_complete_gold_set_rejects_unlinked_true_positive() -> None:
    with pytest.raises(ValidationError, match="every TP finding"):
        SurveyAuditBenchmarkScorecard(
            gold_set_complete=True,
            gold_anomalies=[
                SurveyAuditGoldAnomaly(
                    id="missing-roof",
                    category="omission",
                )
            ],
            runs=[
                SurveyAuditBenchmarkRun(
                    run_id="run-1",
                    contract_valid=True,
                    audit_status="needs_correction",
                    findings=[_finding("unlinked-roof")],
                    missed_gold_anomaly_ids=["missing-roof"],
                )
            ],
        )


def test_run_rejects_multiple_true_positives_for_same_gold_anomaly() -> None:
    with pytest.raises(ValidationError, match="label duplicate detections as DUP"):
        SurveyAuditBenchmarkRun(
            run_id="run-1",
            contract_valid=True,
            audit_status="needs_correction",
            findings=[
                _finding("roof-a", gold_anomaly_id="missing-roof"),
                _finding("roof-b", gold_anomaly_id="missing-roof"),
            ],
        )
