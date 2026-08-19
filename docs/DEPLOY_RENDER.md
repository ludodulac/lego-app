# Deploy BrickHouse API on Render

BrickHouse keeps the static frontend on GitHub Pages and deploys the Python/FastAPI engine separately as a Render Web Service.

## Why this split

- GitHub Pages serves the public static viewer/configurator/photo UI.
- Render runs `brickhouse.api:app` and keeps server secrets out of the browser.
- `OPENAI_API_KEY` exists only in the Render service environment.
- Browser photo uploads go to BrickHouse API, which then calls OpenAI server-side.

## Repository configuration

The repository contains both a portable `Dockerfile` and a Render Blueprint (`render.yaml`). The Render service can use the native Python runtime defined by the Blueprint.

Start command:

```bash
uvicorn brickhouse.api:app --host 0.0.0.0 --port $PORT
```

Health check:

```text
/health
```

## Required server variables

`OPENAI_API_KEY`
: Secret OpenAI API key. Never put this value in GitHub Pages, frontend JavaScript, source control, screenshots, issues, or chat messages.

`OPENAI_VISION_MODEL`
: Defaults to `gpt-5`. It can be changed server-side without changing the frontend.

`BRICKHOUSE_CORS_ORIGINS`
: Comma-separated allowed browser origins. For the current prototype: `https://ludodulac.github.io`.

## First deployment

1. In Render, create a Blueprint or Web Service from `ludodulac/lego-app` on branch `main`.
2. If using the Blueprint, Render reads `render.yaml`.
3. Set the secret `OPENAI_API_KEY` in Render when prompted.
4. Deploy and wait for `/health` to become healthy.
5. Copy the generated HTTPS service URL, for example `https://brickhouse-api-xxxx.onrender.com`.
6. Open the BrickHouse photo page on GitHub Pages and paste that base URL into **URL API BrickHouse**. The page stores it locally in the browser.
7. Test `/health`, then a normal BuildingModel build, then a one-photo analysis.

## Security boundary

The frontend never receives the OpenAI API key. It sends images to the BrickHouse API only. The API performs image validation, calls the OpenAI Responses API, validates the structured result as `PhotoAnalysisResult`, and returns a proposed `BuildingModel` plus uncertainty metadata.

The current prototype does not persist uploaded photos or analysis results in a database. A future project/storage layer will define retention and deletion explicitly before user accounts are introduced.

## Portable deployment

The root `Dockerfile` can also be used on Railway, Fly.io, Cloud Run, or another container platform. The container expects a `PORT` environment variable and exposes the same `/health` endpoint.
