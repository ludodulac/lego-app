from pathlib import Path


def test_render_blueprint_targets_fastapi_and_healthcheck():
    text = Path("render.yaml").read_text(encoding="utf-8")
    assert "uvicorn brickhouse.api:app" in text
    assert "--host 0.0.0.0" in text
    assert "--port $PORT" in text
    assert "healthCheckPath: /health" in text
    assert "plan: free" in text
    # Vision is deliberately optional in the zero-cost prototype deployment.
    assert "OPENAI_API_KEY" not in text


def test_dockerfile_runs_same_api_contract():
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in text
    assert "pip install ." in text
    assert "uvicorn brickhouse.api:app" in text
    assert "${PORT}" in text


def test_deployment_docs_do_not_embed_a_key():
    text = Path("docs/DEPLOY_RENDER.md").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY" in text
    assert "sk-" not in text
