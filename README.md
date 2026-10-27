# Food Journal

A FastAPI backend for a personal food journal.

## Setup

Use Python 3.13, then create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Database

The app uses PostgreSQL 18, installed with Homebrew. It runs as your macOS user, so no password is needed.

Install it once, then create the database and the tables:

```bash
brew install postgresql@18
brew services start postgresql@18
createdb food_journal
```

Create a `.env` file in the project root with the connection string:

```bash
DATABASE_URL=postgresql+psycopg://<your-macos-username>@localhost:5432/food_journal
```

Create the tables from the models:

```bash
.venv/bin/python -c "from app.database import Base, engine; import app.models; Base.metadata.create_all(engine)"
```

Start the server (it also starts automatically with `./scripts/dev.sh`):

```bash
brew services start postgresql@18
```

Check that it is accepting connections:

```bash
/opt/homebrew/opt/postgresql@18/bin/pg_isready -h localhost -p 5432
```

Connect with `psql` and inspect the data:

```bash
/opt/homebrew/opt/postgresql@18/bin/psql -d food_journal
```

```sql
\dt                              -- list tables
\d posts                         -- show the posts table
SELECT * FROM posts;             -- show all posts
\q                               -- quit psql
```

Stop the server when you are done:

```bash
brew services stop postgresql@18
```

Start the database before running the app. Stopping the database also disconnects the app.

## Run locally

Start the database and the app together:

```bash
./scripts/dev.sh
```

The script starts PostgreSQL if it isn't running, runs the app, and stops PostgreSQL when you quit the app with Ctrl+C.

To run the app without the script, start the database first and then run:

```bash
uvicorn app.main:app --reload
```

The API docs are available at http://127.0.0.1:8000/docs.

## Run tests

Tests use the `food_journal_test` database. Create it once with `createdb food_journal_test`, then run:

```bash
DATABASE_URL=postgresql+psycopg://<your-macos-username>@localhost:5432/food_journal_test python -m pytest
```

The tests refuse to run unless `DATABASE_URL` points at a database whose name ends in `_test`.
