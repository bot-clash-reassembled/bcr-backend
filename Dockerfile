FROM python:3.12 AS builder

ENV PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

RUN pip install poetry==2.4.3

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --without dev
RUN .venv/bin/python -m pip uninstall pip -y

FROM python:3.12-slim AS prod

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=src

WORKDIR /app
COPY --from=builder /app /app
COPY . /app

EXPOSE 8000
CMD [".venv/bin/uvicorn", "src.entrypoints.web_api:app", "--host", "0.0.0.0", "--port", "8000"]
