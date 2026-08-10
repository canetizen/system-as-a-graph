FROM python:3.11-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

# MSD's source repository adapter drives the real git client, so the image
# carries it. Everything else the CSUs need is a Python package.
RUN apt-get update \
    && apt-get install --no-install-recommends -y git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

# The workspace root plus every member's own distribution metadata and sources.
# Each member is installed as a separate distribution, so this list is the only
# place the image knows which CSUs exist.
COPY pyproject.toml uv.lock .python-version ./
COPY contracts ./contracts
COPY platform_host ./platform_host
COPY msd ./msd
COPY scg ./scg
COPY frd ./frd
COPY adp ./adp
COPY csm ./csm
COPY vae ./vae

FROM base AS dev

# Editable installs so the bind-mounted source in compose.dev.yml is the source
# of truth: each member's .pth entry points at /app/<member>/src.
RUN uv sync --frozen --inexact

COPY tests ./tests

CMD ["uvicorn", "saag_platform.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod

RUN uv sync --frozen --inexact --no-dev --no-editable

RUN useradd --create-home appuser
USER appuser

CMD ["saag-api"]
