FROM python:3.11-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/

# git is needed twice over: MSD's source repository adapter drives the real client,
# and the CSU distributions are themselves resolved from repositories until there
# is an index to publish them to (CDR-31).
RUN apt-get update \
    && apt-get install --no-install-recommends -y git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

# Only this repository is copied. Which CSUs the image contains is decided by the
# lock file, not by what happens to be on the build host.
COPY pyproject.toml uv.lock .python-version ./

FROM base AS dev

RUN uv sync --frozen --inexact

COPY tests ./tests

CMD ["uvicorn", "saag_platform.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod

RUN uv sync --frozen --inexact --no-dev --no-editable

RUN useradd --create-home appuser
USER appuser

CMD ["saag-api"]
