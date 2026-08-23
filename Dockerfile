FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY backend ./backend
COPY data/processed ./data/processed

RUN python -m pip install --upgrade pip && python -m pip install .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn brickhouse.api:app --host 0.0.0.0 --port ${PORT}"]
