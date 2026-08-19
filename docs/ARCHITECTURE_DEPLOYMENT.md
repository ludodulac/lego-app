# BrickHouse prototype deployment architecture

```text
GitHub Pages
  frontend/index.html          viewer 3D
  frontend/instructions.html   instructions
  frontend/configurator.html   manual BuildingModel input
  frontend/photo.html          photo + clarification workflow
          |
          | HTTPS (CORS restricted)
          v
Render Web Service
  brickhouse.api:app
    GET  /health
    POST /api/v1/build
    POST /api/v1/analyze-photos
          |
          | server-side only
          v
OpenAI Responses API
  image analysis -> PhotoAnalysisResult -> BuildingModel
          |
          v
BrickHouse deterministic engine
  BuildingModel -> geometry -> constructible BrickModel -> BOM -> AssemblyPlan
```

## Current prototype boundaries

- Source code and CI: GitHub.
- Static public UI: GitHub Pages.
- Dynamic Python engine and photo-analysis gateway: Render.
- AI provider credentials: Render environment secret only.
- No database is required for the first end-to-end photo test.
- No uploaded photo persistence is implemented in M0.

## Next infrastructure layer

Supabase becomes useful after the first live photo test, when BrickHouse needs persistent projects, authentication, original/reference photos, BuildingModel revisions, generated exports, and user-owned history. It is deliberately not required to prove the core photo -> model -> bricks loop.
