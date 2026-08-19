# BrickHouse Engine HTTP API

BH-029 exposes the existing deterministic engine through a small FastAPI boundary. This is the contract the future configurator and photo-analysis workflow can call after they have produced a valid `BuildingModel`.

## Run locally

Install the project with development dependencies, then start Uvicorn:

```bash
python -m pip install -e ".[dev]"
uvicorn brickhouse.api:app --host 0.0.0.0 --port 8000
```

The interactive OpenAPI documentation is then available at `/docs` and the health endpoint at `/health`.

## Build endpoint

`POST /api/v1/build`

Request shape:

```json
{
  "building": { "...": "BuildingModel v0.1" },
  "front_width_studs": 48
}
```

`front_width_studs` is optional and defaults to 48.

Successful response: the canonical BrickHouse export bundle containing:

- `brick_model`
- `bom`
- `assembly_plan`

The endpoint uses the same Python pipeline as the CLI. There is no second implementation of the building-to-bricks logic.

## Validation

Pydantic validates the `BuildingModel` request before the engine runs. Invalid request contracts return HTTP 422. Engine-level constructibility failures are also surfaced as HTTP 422 with a readable `detail` message.

## CORS

By default the API accepts the current GitHub Pages origin plus local development origins. Production deployments can override this with a comma-separated `BRICKHOUSE_CORS_ORIGINS` environment variable.

## Product architecture

The intended future flow is:

```text
photos + user text
        ↓
AI / reconstruction layer
        ↓
BuildingModel v0.1
        ↓
POST /api/v1/build
        ↓
BrickModel + BOM + AssemblyPlan
        ↓
viewer / instructions / purchasing
```

The AI layer should not directly place bricks. Its responsibility is to produce and refine the architectural `BuildingModel`; the engine API remains the single source of truth for constructible brick output.
