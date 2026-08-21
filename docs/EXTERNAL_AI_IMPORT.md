# External AI analysis import

BrickHouse must not depend on one vision provider in order to test or use the downstream LEGO pipeline.

## Reference manual workflow: ChatGPT

For MVP photo trials, ChatGPT is the reference external analyzer. This is a workflow choice, not a provider dependency: the JSON contract remains provider-independent.

1. Start a new ChatGPT conversation.
2. Attach all useful photos of the same building.
3. Paste `frontend/brickhouse-ai-prompt.txt` unchanged.
4. In the same message or immediately after it, provide only the known facts/measurements (for example: `Façade avant = 10 m. Le toit n'est pas photographié du dessus. N'invente pas les zones cachées.`).
5. ChatGPT must return one `PhotoAnalysisResult` JSON object only, with no prose or Markdown around it.
6. Paste that JSON into the BrickHouse photo page.
7. BrickHouse posts it to `POST /api/v1/validate-analysis`, validates the Pydantic contract and recomputes `m0_compatibility` itself.
8. Review questions, assumptions, scale evidence and M0 blockers before building.
9. A validated, buildable proposal can flow to `POST /api/v1/build`, then BrickModel, BOM, AssemblyPlan, viewer and printable instructions.

If ChatGPT adds explanatory prose despite the prompt, keep the JSON object only before importing. This is considered a provider-format defect, not architectural evidence.

## Why ChatGPT is the reference workflow

Using one repeatable manual workflow makes photo trials comparable while the architectural contract is still evolving. The integrated API provider remains an optional automation layer and must not change the meaning of the contract.

The same prompt can still be tested with Claude, Gemini or another multimodal model when useful. BrickHouse should never require provider-specific fields.

## Contract discipline learned from the first real house trial

The current import contract remains `PhotoAnalysisResult 0.3` / `BuildingModel 0.1`. It is deliberately not yet the final general architectural scene language.

Important interpretation rules:

- A user-provided anchor such as a 10 m facade width does not make an entire volume `user_provided` when depth, height or floor count are inferred.
- `volume.height` is wall/prism height up to the roof support/eaves level; it is not total ridge height. Roof geometry is represented separately.
- Repeated rows of openings do not by themselves prove the number of full floors.
- Hidden facades and roof zones must stay uncertain; symmetry must not be invented.
- Unsupported elements such as open stairs, terraces, balconies on posts and complex roofs must be described as limitations rather than silently converted into solid rectangular building volumes.
- `m0_compatibility` is always null in external output. Only BrickHouse decides whether M0 can build the proposal.

Future `ArchitecturalScene` versions may add per-property provenance, wall/eaves/ridge height semantics, terraces, stairs, balconies, general primitives, rotations, curved/free-form surfaces and richer relationships. These additions should be driven by repeated real-photo failures rather than speculative schema growth.

## Reproducibility

Keep the original photos, known measurements, raw AI response, validated BrickHouse result and engine revision for each trial. Re-run the same photo set after prompt/contract changes before moving to a new building; this makes regressions visible.