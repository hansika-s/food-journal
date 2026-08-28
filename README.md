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

## Run locally

```bash
uvicorn app.main:app --reload
```

Visit http://127.0.0.1:8000/health.

## Run tests

```bash
python -m pytest
```
