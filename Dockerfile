FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* README.md ./
COPY src ./src
COPY configs ./configs

RUN uv sync --frozen --no-dev 2>/dev/null || uv sync --no-dev

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data /app/models/registry/aliases /app/reports \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["uvicorn", "churnops.api:app", "--host", "0.0.0.0", "--port", "8000"]

