# External AI analysis import

BrickHouse must not depend on one vision provider in order to test or use the downstream LEGO pipeline.

## Reference manual workflow: ChatGPT, two passes

For real-photo trials, ChatGPT is the reference external analyzer. This is a workflow choice, not a provider dependency: the JSON contract remains provider-independent.

### Pass A — ArchitecturalScene reconstruction

1. Start a new ChatGPT conversation.
2. Attach all useful photos of the same building in a stable order.
3. Paste `frontend/brickhouse-ai-prompt.txt` unchanged.
4. Provide reliable photo labels/orientations and only known facts/measurements.
5. ChatGPT returns one candidate `ArchitecturalScene` v0.2 JSON object only.

The v0.2 scene is intentionally richer than the current LEGO engine. It may retain terrain/grade, chimney, terrace/platform, support posts, stairs, facade equipment and occlusions even when M0 cannot construct them yet.

### Pass B — contradictory validation

6. Start a SECOND new ChatGPT conversation so the audit is not anchored to the reconstruction conversation.
7. Attach the same photos in the same order.
8. Paste the candidate ArchitecturalScene JSON from Pass A.
9. Paste `frontend/brickhouse-ai-validation-prompt.txt` unchanged.
10. The validator treats the candidate as untrusted, re-checks building boundaries and every scene object against independent visual evidence, and returns one corrected complete ArchitecturalScene v0.2 JSON object only.
11. It may remove unsupported/unproved openings and may add clearly visible scene elements that Pass A omitted, such as chimney, grade profile, terrace, stairs, equipment or occlusion spans.

### BrickHouse scene validation and projection

12. POST the Pass B scene to `POST /api/v1/validate-scene`.
13. BrickHouse validates ArchitecturalScene v0.2 and returns both the accepted `scene` and a structured `projection` toward BuildingModel 0.1.
14. Projection issues make information loss explicit. Current examples: terrain, chimneys, platforms and stairs can be retained in the scene while being omitted from BuildingModel 0.1 with warnings.
15. True M0 incompatibilities such as unsupported volume/roof counts are blockers, not silent geometry edits.
16. If `projection.building` is present and compatible, it can flow into `POST /api/v1/build` for the current BrickModel/BOM/AssemblyPlan pipeline.
17. Compare the generated model facade-by-facade against the original photos. Visual disagreement is regression evidence, not something to hide by changing the source scene silently.

Legacy `POST /api/v1/validate-analysis` remains available for PhotoAnalysisResult 0.3 / BuildingModel 0.1 imports during migration.

If an AI adds explanatory prose despite the prompt, keep the JSON object only before importing. This is a provider-format defect, not architectural evidence.

## Why two passes

The first real house trial showed that a capable multimodal model can understand the overall architecture while still misclassifying an individual opening, extending a facade beyond the actual building boundary, inventing rear openings, missing a chimney or flattening terrain context.

Asking the reconstruction conversation merely to "check itself" risks repeating the same anchored interpretation. The second conversation therefore acts as an adversarial auditor and must use photos/user facts as stronger evidence than the candidate JSON.

This does not make the result infallible. Ambiguous photos may still produce the same mistake twice. The goal is to reduce silent hallucination and preserve uncertainty, not claim photogrammetric truth.

## Contract discipline learned from the real-house trial

ArchitecturalScene v0.2 sits above BuildingModel 0.1:

`photos -> Pass A -> Pass B -> ArchitecturalScene v0.2 -> validate/project -> BuildingModel 0.1 -> M0`

Key rules:

- provenance for volume width/depth/height is property-level;
- `volume.height` is wall/eaves-support height, not ridge height;
- terrain/road slope is represented through facade grade profiles when useful;
- low openings may record local-grade clearance independently of global z;
- facade boundaries and visibility/occlusion spans are first-class evidence constraints;
- openings in occluded/unknown spans are invalid;
- neighboring buildings remain context, not target geometry;
- chimney, raised platform/supports and exterior stairs remain first-class scene objects instead of fake solid volumes;
- utility boxes, pipes, gutters/downspouts, vents and temporary objects can be preserved as semantic equipment observations to prevent misclassification;
- `ridge_direction` is the ridge axis: `depth` front-to-rear, `width` left-to-right;
- projection losses must be explicit before construction.

## Reproducibility

Keep original photos outside the repository when privacy/provenance requires it, but keep a derived semantic regression fixture containing only the facts needed to reproduce schema/projection behavior. For each trial preserve: photo order/labels, known measurements, raw Pass A, raw Pass B, accepted ArchitecturalScene, projection result and engine revision.
