# SurveyAudit triplet — deterministic replay result

Date: 2026-09-02
Source handoff: `docs/private-benchmark-handoff/SURVEY_AUDIT_TRIPLET_2026-09-02.md`
Survey source id: `brickhouse-survey`

## Privacy boundary

No source PDF, photo, or ArchitecturalSurvey payload is recorded here. The private inputs remain outside the repository.

## Replay basis

The three raw outputs were checked **without editing, normalizing, deduplicating, or correcting them**, against the current `SurveyAudit v0.1` contract on `main`.

The current contract requires every `photo_evidence` entry to be a `PhotoEvidence` object with at least:

```json
{"photo_index": 1, "observation": "<visible evidence>"}
```

The dedicated audit prompt specifies the same object shape.

## Result

All three raw outputs are contract-invalid before semantic `validate_survey_audit(...)` replay can run:

| run | declared findings | contract result | first blocking shape error |
| --- | ---: | --- | --- |
| Run 1 | 8 | invalid | `photo_evidence` entries are strings, not `PhotoEvidence` objects |
| Run 2 | 6 | invalid | `photo_evidence` entries are strings, not `PhotoEvidence` objects |
| Run 3 | 8 | invalid | `photo_evidence` entries are strings, not `PhotoEvidence` objects |

Because `SurveyAudit.findings[].photo_evidence` is typed as `list[PhotoEvidence]`, each run fails Pydantic parsing at the first string evidence entry. This is a contract failure, not an adjudication result, and the raw JSON must not be repaired for benchmark inclusion.

## Benchmark consequence

Per `docs/SURVEY_AUDIT_BENCHMARK_V01.md`, an invalid audit contract is a failed run and must not be hand-corrected. Therefore these three outputs cannot satisfy the formal Phase 2 requirement for three replayable independent SurveyAudit runs.

Do **not** proceed to exhaustive gold recall/F1 scoring or to SurveyCorrection from these outputs. The benchmark remains open until three new independent raw outputs are produced in the exact `SurveyAudit v0.1` shape and replay successfully without edits.

The earlier malformed/cannot-execute attempts remain excluded exactly as required by the handoff.

## Exact next step

1. Keep the same frozen private PDF/photos and ArchitecturalSurvey.
2. Produce at least three new audits in genuinely separate fresh contexts using `frontend/brickhouse-survey-independent-audit-v01.txt` unchanged.
3. Preserve each raw JSON byte-for-byte.
4. Replay each raw JSON without edits through the repository validator/boundary.
5. Only after all retained runs are contract-valid, build the exhaustive gold annotation independently of those outputs and run the executable scorecard.
6. Only if GO thresholds remain satisfied, continue with automatically eligible `SurveyCorrection` findings followed by bounded `SurveyCorrectionReaudit`.

No application behavior or validator was changed by this replay.