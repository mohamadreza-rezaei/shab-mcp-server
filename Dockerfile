FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SHAB_MCP_HOST=0.0.0.0 \
    SHAB_MCP_PORT=8000 \
    SHAB_MCP_TRANSPORT=http \
    UV_LINK_MODE=copy

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv

COPY pyproject.toml README.md ./
COPY src ./src

# Install project (avoid pip hash-mismatch flakes on transitive wheels).
RUN uv pip install --system --no-cache .

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["shab-mcp"]
