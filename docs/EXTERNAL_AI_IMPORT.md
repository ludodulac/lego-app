# External AI analysis import

BrickHouse must not depend on one vision provider in order to test or use the downstream LEGO pipeline.

## Reference manual workflow: ChatGPT, two passes

For MVP photo trials, ChatGPT is the reference external analyzer. This is a workflow choice, not a provider dependency: the JSON contract remains provider-independent.

### Pass A — architectural reconstruction

1. Start a new ChatGPT conversation.
2. Attach all useful photos of the same building in a stable order.
3. Paste `frontend/brickhouse-ai-prompt.txt` unchanged.
4. Provide reliable photo labels/orientations and only known facts/measurements.
5. ChatGPT returns one candidate `PhotoAnalysisResult` JSON object only.

### Pass B — contradictory validation

6. Start a SECOND new ChatGPT conversation so the audit is not anchored to the reconstruction conversation.
7. Attach the same photos in the same order.
8. Paste the candidate JSON from Pass A.
9. Paste `frontend/brickhouse-ai-validation-prompt.txt` unchanged.
10. The validator must treat the candidate JSON as untrusted, seek independent visual evidence for every opening/volume/roof and output one corrected complete `PhotoAnalysisResult` JSON only.
11. Prefer deletion or lower confidence over keeping an unproved object. The validation pass is not a guarantee: ambiguous images may still produce the same mistake twice.

### BrickHouse validation and build

12. Paste the Pass B JSON into the BrickHouse photo page.
13. BrickHouse posts it to `POST /api/v1/validate-analysis`, validates the Pydantic contract and recomputes `m0_compatibility` itself.
14. Review questions, assumptions, scale evidence and M0 blockers before building.
15. A validated, buildable proposal can flow to `POST /api/v1/build`, then BrickModel, BOM, AssemblyPlan, viewer and printable instructions.
16. Compare the generated model back to the original photos. Visual/model disagreement is evidence for the next prompt/schema/engine iteration.

If an AI adds explanatory prose despite the prompt, keep the JSON object only before importing. This is considered a provider-format defect, not architectural evidence.

## Why two passes

The first real house trial showed that a capable multimodal model can correctly understand overall architecture while still misclassifying an individual opening, assigning an opening to the wrong facade or producing unstable depth/height estimates. Asking the reconstruction conversation merely to "check itself" risks repeating the same anchored interpretation.

The second pass therefore has a different role: adversarial auditor rather than reconstructor. It must require independent visual support object by object and use the user-provided photo orientations as higher-priority evidence than the candidate JSON.

This does not make the result infallible. If both passes agree on something genuinely ambiguous, the user/model review stage must still be able to correct it. The goal is to reduce silent hallucination, not claim automatic photogrammetric truth.

## Why ChatGPT is the reference workflow

Using one repeatable manual workflow makes photo trials comparable while the architectural contract is still evolving. The integrated API provider remains an optional automation layer and must not change the meaning of the contract.

The same prompts can still be tested with Claude, Gemini or another multimodal model when useful. BrickHouse should never require provider-specific fields.

## Contract discipline learned from the first real house trial

The current import contract remains `PhotoAnalysisResult 0.3` / `BuildingModel 0.1`. It is deliberately not yet the final general architectural scene language.

Important interpretation rules:

- A user-provided anchor such as a 10 m facade width does not make an entire volume `user_provided` when depth, height or floor count are inferred.
- `volume.height` is wall/prism height up to the roof support/eaves level; it is not total ridge height. Roof geometry is represented separately.
- Repeated rows of openings do not by themselves prove the number of full floors.
- User-provided facade labels/orientations are trusted metadata unless the inputs are manifestly contradictory.
- Every opening should have visual evidence on the labelled facade; uncertain openings should be removed or downgraded rather than completed by symmetry.
- Hidden facades and roof zones must stay uncertain; symmetry must not be invented.
- A neighboring attached building is context/occlusion, not part of the target building unless the user says otherwise.
- Unsupported elements such as open stairs, terraces, balconies on posts and complex roofs must be described as limitations rather than silently converted into solid rectangular building volumes.
- `ridge_direction` means the axis of the ridge: `depth` is front-to-rear, `width` is left-to-right.
- `m0_compatibility` is always null in external output. Only BrickHouse decides whether M0 can build the proposal.

Future `ArchitecturalScene` versions may add per-property provenance, wall/eaves/ridge height semantics, terraces, stairs, balconies, terrain, general primitives, rotations, curved/free-form surfaces and richer relationships. These additions should be driven by repeated real-photo failures rather than speculative schema growth.

## Reproducibility

Keep the original photos, photo labels, known measurements, raw Pass A response, raw Pass B response, validated BrickHouse result and engine revision for each trial. Re-run the same photo set after prompt/contract changes before moving to a new building; this makes regressions visible.