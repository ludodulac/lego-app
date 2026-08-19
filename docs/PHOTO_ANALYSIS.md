# Photo analysis M0

BH-031 is the first implementation of BrickHouse's core product promise: multiple property photos plus user text produce an architectural proposal that can then be converted by the existing constructible brick engine.

## Boundary

The AI layer does **not** place bricks. It produces a `PhotoAnalysisResult` containing:

- a complete proposed `BuildingModel v0.1`;
- clarification questions;
- explicit assumptions;
- an overall confidence score;
- `needs_confirmation` when important uncertainty remains.

The confirmed `BuildingModel` is then sent to the existing `/api/v1/build` endpoint.

## M0 architectural scope

The first vision prototype intentionally matches the current engine scope:

- one main rectangular detached-house volume;
- gable roof;
- exterior doors and windows that materially affect the miniature;
- conservative completion of hidden sides.

If the rear or a side is not visible, the provider is instructed to prefer a simple rectangular continuation rather than inventing an elaborate hidden structure. Significant uncertainty should create a clarification question.

## Source provenance

Every architectural fact already has a `SourceInfo` contract. Photo analysis must use it consistently:

- `observed`: clearly visible in supplied photos;
- `user_provided`: supplied in notes or known measurements;
- `inferred`: reconstructed from visible geometry;
- `generated_default`: deliberate fallback where a complete proposal is needed despite missing information.

This provenance remains inside the `BuildingModel` so later UI can explain what BrickHouse actually knows.

## HTTP endpoint

`POST /api/v1/analyze-photos` uses `multipart/form-data`.

Fields:

- `photos`: 1 to 6 JPEG, PNG or WebP files;
- `user_notes`: optional free text;
- `known_front_width_m`: optional positive metric scale anchor.

Current per-photo server limit: 12 MiB.

The endpoint returns `PhotoAnalysisResult`.

## OpenAI provider

The server-side provider uses the OpenAI Responses API with multiple `input_image` content items. Images are converted to base64 data URLs on the server request. A JSON Schema response format is supplied and the resulting JSON is validated again with Pydantic before BrickHouse accepts it.

Environment:

```bash
export OPENAI_API_KEY="..."
export OPENAI_VISION_MODEL="gpt-5.6-terra"   # optional override
```

`OPENAI_VISION_MODEL` defaults to `gpt-5.6-terra` in this prototype. The provider is isolated so model choice can change without changing `BuildingModel` or the brick engine.

## Security and privacy boundary

The OpenAI API key must exist only in the server environment. It must never be placed in `frontend/`, GitHub Pages, browser localStorage, or a client-side request.

The browser sends property photos to the BrickHouse backend. The backend validates file type/size and then sends the image inputs to the configured AI provider.

Production work should add project/user authentication, storage/retention controls, deletion policies, rate limits, upload malware/content safeguards where appropriate, and a clear privacy notice before users upload private property photos.

## Frontend

`frontend/photo.html` supports:

1. choosing/taking 1–6 property photos;
2. optional explanatory text;
3. optional known facade width;
4. displaying confidence, clarification questions and assumptions;
5. inspecting/downloading the proposed `BuildingModel`;
6. sending that model to `/api/v1/build`;
7. opening the returned brick model in the existing viewer.

At this stage the page displays questions but does not yet feed the user's answers back into a second AI refinement pass. That conversational correction loop is the next layer.
