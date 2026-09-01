"""Reproducible scorecard helpers for the SurveyAudit benchmark.

This module deliberately stores adjudication metadata, not private photos or
Survey payloads. Recall/F1 stay unavailable until an exhaustive gold set is
explicitly declared complete.
"""

from __future__ import annotations

from collections import Counter
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .audit import SurveyAuditStatus


class SurveyAuditBenchmarkLabel(str, Enum):
    TP = "TP"
    FP = "FP"
    DUP = "DUP"
    NEI = "NEI"


class SurveyAuditBenchmarkCategory(str, Enum):
    PHYSICAL_IDENTITY = "physical_identity"
    OMISSION = "omission"
    FALSE_POSITIVE = "false_positive"
    ORIENTATION_OR_SIDE = "orientation_or_side"
    CERTAINTY_CALIBRATION = "certainty_calibration"
    RELATION = "relation"
    CROSS_VIEW_CONTRADICTION = "cross_view_contradiction"
    NON_ACTIONABLE = "non_actionable"


class SurveyAuditFindingAdjudication(BaseModel):
    finding_id: str = Field(min_length=1)
    label: SurveyAuditBenchmarkLabel
    category: SurveyAuditBenchmarkCategory
    actionable: bool
    evidence_supported: bool
    deterministic_overlap: bool = False
    gold_anomaly_id: str | None = None

    @model_validator(mode="after")
    def validate_gold_link(self) -> "SurveyAuditFindingAdjudication":
        if self.label is SurveyAuditBenchmarkLabel.TP and self.actionable:
            if self.gold_anomaly_id is not None and not self.gold_anomaly_id.strip():
                raise ValueError("gold_anomaly_id must be non-empty when provided")
        elif self.gold_anomaly_id is not None:
            raise ValueError("only TP findings may reference gold_anomaly_id")
        return self


class SurveyAuditBenchmarkRun(BaseModel):
    run_id: str = Field(min_length=1)
    contract_valid: bool
    audit_status: SurveyAuditStatus
    findings: list[SurveyAuditFindingAdjudication] = Field(default_factory=list)
    missed_gold_anomaly_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_finding_ids(self) -> "SurveyAuditBenchmarkRun":
        ids = [item.finding_id for item in self.findings]
        if len(ids) != len(set(ids)):
            raise ValueError("benchmark finding ids must be unique within a run")
        if len(self.missed_gold_anomaly_ids) != len(set(self.missed_gold_anomaly_ids)):
            raise ValueError("missed_gold_anomaly_ids must be unique within a run")
        return self


class SurveyAuditBenchmarkScorecard(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    kind: Literal["survey_audit_benchmark_scorecard"] = (
        "survey_audit_benchmark_scorecard"
    )
    runs: list[SurveyAuditBenchmarkRun] = Field(min_length=1)
    gold_set_complete: bool = False
    gold_anomaly_ids: list[str] = Field(default_factory=list)
    user_truth_changes_without_contradiction: int = Field(default=0, ge=0)
    status_flip_without_evidence: bool = False

    @model_validator(mode="after")
    def validate_gold_set(self) -> "SurveyAuditBenchmarkScorecard":
        run_ids = [run.run_id for run in self.runs]
        if len(run_ids) != len(set(run_ids)):
            raise ValueError("benchmark run ids must be unique")
        if len(self.gold_anomaly_ids) != len(set(self.gold_anomaly_ids)):
            raise ValueError("gold_anomaly_ids must be unique")
        if self.gold_set_complete and not self.gold_anomaly_ids:
            raise ValueError("a complete gold set must contain at least one anomaly")
        known = set(self.gold_anomaly_ids)
        if known:
            for run in self.runs:
                referenced = {
                    item.gold_anomaly_id
                    for item in run.findings
                    if item.gold_anomaly_id is not None
                } | set(run.missed_gold_anomaly_ids)
                unknown = referenced - known
                if unknown:
                    raise ValueError(
                        "benchmark run references unknown gold anomalies: "
                        + ", ".join(sorted(unknown))
                    )
        return self


class SurveyAuditBenchmarkMetrics(BaseModel):
    total_findings: int
    tp: int
    fp: int
    dup: int
    nei: int
    precision: float | None
    recall: float | None
    f1: float | None
    duplicate_rate: float
    actionable_precision: float | None
    evidence_precision: float | None
    deterministic_overlap_rate: float | None
    net_new_true_findings: int | None
    correction_trigger_rate: float
    contract_valid_rate: float
    status_agreement: float


class SurveyAuditBenchmarkDecision(BaseModel):
    go_experimental: bool
    blockers: list[str] = Field(default_factory=list)


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def compute_survey_audit_benchmark_metrics(
    scorecard: SurveyAuditBenchmarkScorecard,
) -> SurveyAuditBenchmarkMetrics:
    findings = [item for run in scorecard.runs for item in run.findings]
    counts = Counter(item.label for item in findings)
    tp = counts[SurveyAuditBenchmarkLabel.TP]
    fp = counts[SurveyAuditBenchmarkLabel.FP]
    dup = counts[SurveyAuditBenchmarkLabel.DUP]
    nei = counts[SurveyAuditBenchmarkLabel.NEI]
    precision = _ratio(tp, tp + fp + dup)

    actionable = [item for item in findings if item.actionable]
    actionable_tp = sum(
        item.label is SurveyAuditBenchmarkLabel.TP for item in actionable
    )
    actionable_precision = _ratio(actionable_tp, len(actionable))

    evidence_decidable = [
        item for item in findings if item.label is not SurveyAuditBenchmarkLabel.NEI
    ]
    evidence_precision = _ratio(
        sum(item.evidence_supported for item in evidence_decidable),
        len(evidence_decidable),
    )

    tp_findings = [item for item in findings if item.label is SurveyAuditBenchmarkLabel.TP]
    deterministic_overlap_rate = _ratio(
        sum(item.deterministic_overlap for item in tp_findings),
        len(tp_findings),
    )

    gold_tp_ids = {
        item.gold_anomaly_id
        for item in tp_findings
        if item.gold_anomaly_id is not None
    }
    recall: float | None = None
    f1: float | None = None
    if scorecard.gold_set_complete:
        recall = _ratio(len(gold_tp_ids), len(scorecard.gold_anomaly_ids))
        if precision is not None and recall is not None and precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)

    net_new_ids = {
        item.gold_anomaly_id
        for item in tp_findings
        if item.actionable
        and not item.deterministic_overlap
        and item.gold_anomaly_id is not None
    }
    net_new_true_findings = len(net_new_ids) if gold_tp_ids else None

    statuses = Counter(run.audit_status for run in scorecard.runs)
    status_agreement = max(statuses.values()) / len(scorecard.runs)

    return SurveyAuditBenchmarkMetrics(
        total_findings=len(findings),
        tp=tp,
        fp=fp,
        dup=dup,
        nei=nei,
        precision=precision,
        recall=recall,
        f1=f1,
        duplicate_rate=_ratio(dup, len(findings)) or 0.0,
        actionable_precision=actionable_precision,
        evidence_precision=evidence_precision,
        deterministic_overlap_rate=deterministic_overlap_rate,
        net_new_true_findings=net_new_true_findings,
        correction_trigger_rate=(
            sum(run.audit_status is SurveyAuditStatus.NEEDS_CORRECTION for run in scorecard.runs)
            / len(scorecard.runs)
        ),
        contract_valid_rate=(
            sum(run.contract_valid for run in scorecard.runs) / len(scorecard.runs)
        ),
        status_agreement=status_agreement,
    )


def evaluate_survey_audit_experimental_go(
    scorecard: SurveyAuditBenchmarkScorecard,
) -> SurveyAuditBenchmarkDecision:
    """Apply only the explicit GO thresholds from benchmark v0.1.

    Recall/F1 are intentionally not GO thresholds yet, but remain unavailable
    until a complete gold set exists. net_new_true_findings requires stable gold
    anomaly IDs so repeated detections across runs are not over-counted.
    """
    metrics = compute_survey_audit_benchmark_metrics(scorecard)
    blockers: list[str] = []

    if metrics.actionable_precision is None or metrics.actionable_precision < 0.80:
        blockers.append("actionable_precision_below_0_80")
    if metrics.evidence_precision is None or metrics.evidence_precision < 0.90:
        blockers.append("evidence_precision_below_0_90")
    if metrics.duplicate_rate > 0.15:
        blockers.append("duplicate_rate_above_0_15")
    if metrics.net_new_true_findings is None:
        blockers.append("net_new_true_findings_not_reproducible")
    elif metrics.net_new_true_findings < 2:
        blockers.append("fewer_than_two_net_new_true_findings")
    if metrics.contract_valid_rate < 1.0:
        blockers.append("not_all_runs_contract_valid")
    if scorecard.user_truth_changes_without_contradiction:
        blockers.append("unsupported_user_truth_change")
    if scorecard.status_flip_without_evidence:
        blockers.append("status_flip_without_evidence")

    return SurveyAuditBenchmarkDecision(
        go_experimental=not blockers,
        blockers=blockers,
    )
