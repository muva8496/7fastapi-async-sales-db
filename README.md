# Vellamo Sales DB API

Async FastAPI service that validates sales payloads with Pydantic and persists them to a database through async SQLAlchemy sessions.

## Stack
FastAPI, Pydantic, SQLAlchemy 2.0 (async), aiosqlite, Uvicorn

## Endpoints
- `GET /health` – liveness check
- `POST /sales` – validate JSON and insert a sale (returns `201`)
- `GET /sales` – list stored sales

## Design notes
- Pydantic rejects bad input (negative quantity, unknown payment method) with a `422` before any database work happens.
- Each request gets its own async session via `Depends(get_session)`, so database I/O never blocks the event loop.
- `transaction_id` is unique, so a retried submission can't create a duplicate sale.
- SQLite is for local development. Moving to Postgres means changing `DATABASE_URL` and swapping `aiosqlite` for `asyncpg`; the endpoint code stays the same.

## Run it
```
conda create -n fastapi-db python=3.11 -y
conda activate fastapi-db
pip install fastapi "uvicorn[standard]" sqlalchemy[asyncio] aiosqlite
uvicorn main:app --reload
```
Then open http://127.0.0.1:8000/docs

## Load test results
_To be added._