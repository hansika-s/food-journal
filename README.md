# Food Journal

A food journal to log the places I try and share with friends.

I'm building the API for it.

## Setup

Install [uv](https://docs.astral.sh/uv/), then install the dependencies:

```bash
uv sync
```

Create a `.env` file with `DATABASE_URL` and `JWT_SECRET_KEY`. Make sure PostgreSQL is running, then create the tables:

```bash
uv run alembic upgrade head
```

## Running it

```bash
uv run fastapi dev app/main.py
```
