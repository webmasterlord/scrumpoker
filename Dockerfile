FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /workdir

RUN adduser -D -u 10001 appuser

ENV HOME=/home/appuser \
    UV_CACHE_DIR=/home/appuser/.cache/uv \
    UV_NO_DEV=1 \
    PYTHONUNBUFFERED=1

# Create directories with correct ownership
RUN mkdir -p /home/appuser/.cache/uv /workdir \
    && chown -R 10001:10001 /home/appuser /workdir

COPY --chown=10001:10001 pyproject.toml uv.lock ./
COPY --chown=10001:10001 app/ ./app/
COPY --chown=10001:10001 static/ ./static/

USER 10001:10001

RUN uv sync --frozen --no-dev

ENV PATH="/workdir/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.api.server:app", "--host", "0.0.0.0", "--port", "8000"]