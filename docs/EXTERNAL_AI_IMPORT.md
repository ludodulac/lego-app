# External AI analysis import

BrickHouse must not depend on one vision provider in order to test or use the downstream LEGO pipeline.

## Canonical flow

1. Give the building photos and known measurements to any capable multimodal AI (Claude, ChatGPT, Gemini, etc.).
2. Use `frontend/brickhouse-ai-prompt.txt` unchanged, then append the project-specific notes such as the known facade width.
3. The AI returns one `PhotoAnalysisResult` JSON object only.
4. The BrickHouse photo page posts that JSON to `POST /api/v1/validate-analysis`.
5. The backend validates the full Pydantic contract and **recomputes `m0_compatibility` itself**. External tools are never trusted to declare a model buildable.
6. A validated, buildable proposal can flow directly to `POST /api/v1/build`, then to BrickModel, BOM, AssemblyPlan, viewer and printable instructions.

This means the integrated API provider is an automation layer, not part of the core architectural contract.

## Why this exists

The MVP should validate the architectural data contract and LEGO engine before paying for a production vision API. A manual external-AI bridge also provides a reference workflow when an integrated provider is down, rate-limited or incompatible with structured output.

## Contract discipline

The current import contract is deliberately the existing `PhotoAnalysisResult` / `BuildingModel v0.1`. It is **not** the final general architectural scene language. Unsupported free-form geometry must be marked as uncertain/unsupported instead of silently forced into a familiar house shape.

Future `ArchitecturalScene` versions may add general primitives, rotations, curved/free-form surfaces and richer relationships. The importer should remain versioned so older photo trials stay reproducible.
