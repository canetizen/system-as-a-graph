FROM python:3.11-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY main.py ./
COPY msd ./msd
COPY scg ./scg
COPY frd ./frd
COPY adp ./adp
COPY csm ./csm
COPY vae ./vae
COPY shared ./shared

RUN pip install --no-cache-dir .

FROM base AS dev

COPY tests ./tests

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod

RUN useradd --create-home appuser
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
