# Food Journal

A FastAPI backend for a personal food journal. Posts can be created, listed, read, updated and deleted.

## Setup

Requires Python 3.13 and PostgreSQL 18.

```bash
brew install postgresql@18
brew services start postgresql@18
createdb food_journal
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create `.env` in the project root:

```bash
DATABASE_URL=postgresql+psycopg://<your-macos-username>@localhost:5432/food_journal
```

Create the tables by running the migrations:

```bash
.venv/bin/alembic upgrade head
```

To change the schema, edit the models in `app/models.py`, then run `.venv/bin/alembic revision --autogenerate -m "describe the change"`. Review the new file in `alembic/versions/`, then run `.venv/bin/alembic upgrade head`.

## Run

```bash
./scripts/dev.sh
```

The API runs at http://127.0.0.1:8000, with docs at `/docs`.

## Test

```bash
createdb food_journal_test
DATABASE_URL=postgresql+psycopg://<your-macos-username>@localhost:5432/food_journal_test .venv/bin/python -m pytest
```
