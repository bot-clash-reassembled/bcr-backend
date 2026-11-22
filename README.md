# BCR Backend

Backend of Bot Clash: Reassembled (BCR) provides REST API for frontend, handles background matchmaking activities &
provides administration utilities.

## Architecture

Primary components of tech stack:
- Python 3.12
- Poetry 2.4
- FastAPI + Uvicorn
- SQLAlchemy + Alembic + PostgreSQL
- Pydantic

Overall code structure is layered with following top-level packages:
- `api`: API level routers & handlers + FastAPI DI
- `battle`: battle simulation engine
- `core`: overall infra like configuration
- `entrypoints`: entry scripts, for now Web API and matchmaker
- `models`: SQLAlchemy ORM-based data models
- `patch`: tweaked types from dependencies
- `repositories`: repository layer for data access
- `schemas`: API level contracts
- `services`: app logic layer

## How to Run Locally

1. Create venv & install deps via Poetry: `poetry install --no-root`
2. Run infra via separate [repo](https://github.com/bot-clash-reassembled/bcr-infra) - PostgreSQL in particular, so use `docker-compose.database.yml` Compose file.
3. Create `.env` by copying `tpl.env` and provide values with no defaults:
   1. PostgreSQL DSN should be in format `postgresql+asyncpg://%user%:%pass%@localhost:5432/bcr_db`
   2. TG bot ID of `@BCR_dev2_bot` is `8829704061`
   3. Use any random string of 32 chars for JWT secret
4. Apply migrations via `poetry run alembic upgrade head`
5. Provision system users & league using scripts in `admin` folder:
   1. `poetry run python admin/provision_system_users.py`
   2. `poetry run python admin/provision_league.py --league_name %league name%`
6. Specify created league ID as `BCR_GLOBAL_DEFAULT_LEAGUE_ID` setting
7. Run Web API via `poetry run python src/entrypoints/web_api.py` and frontend via [separate repo](https://github.com/bot-clash-reassembled/bcr-frontend)
8. Use frontend to log in via Telegram, create a design from a template, save it
9. Try design in battle or enter tournament
10. Run matchmaker entrypoint to generate battles: `poetry run python src/entrypoints/matchmaker.py`

Ensure `PYTHONPATH` contains `src` when running anything.

## CI and Docker image publishing

GitHub Actions runs the tests on pushes to `master` and on all tag pushes.
Docker images are built and published to Docker Hub, after the tests pass, only for version tags in the form `vX.Y` or `vX.Y.Z` (for example, `v1.2` or `v1.2.3`).
Version components must be non-negative integers without leading zeroes.

Docker Hub repo is [here](https://hub.docker.com/repository/docker/denatwrk/bcr-backend/tags).

## Usage of GeoIP

To support country code initialization upon sign up download & add to repo's root `GeoLite2-Country.mmdb` file from MaxMind.
Lookup is done if `X-Forwarded-For` is present in request containing IP address.
