FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install uv

# Copy dependency files first — changes here invalidate the layer cache
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY . .

# Render injects $PORT; default to 8000 for local docker run
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
