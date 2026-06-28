# Use lightweight Python 3.12 base image
FROM python:3.12-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:0.10.9 /uv /uvx /bin/

WORKDIR /app

# Enable bytecode compilation and offline cache where possible
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Sync dependencies in cacheable layer
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

# Sync the rest of the application
COPY src/ /app/src/
COPY pyproject.toml uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Final runtime image
FROM python:3.12-slim

WORKDIR /app

# Copy the synced virtual environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

# Set environment path to use the virtual environment packages
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default execution entrypoint for ZIP CLI batch processor
ENTRYPOINT ["python", "-m", "src.adapters.cli"]
