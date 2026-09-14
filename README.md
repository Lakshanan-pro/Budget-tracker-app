# Personal Expense Tracking System

A simple Flask + SQLite web application for recording, editing, deleting and reviewing personal expenses.

## Features
- User signup and login
- Add an expense with amount, category, date and description
- View expense history
- Edit and delete expenses
- Filter expenses by date
- Dashboard totals and top spending category
- `/health` endpoint for service health checking
- Structured application logging and basic error handling
- Automated tests using pytest

## Technology Stack
- Python / Flask
- SQLite
- HTML, CSS and JavaScript
- Git and GitHub
- pytest for automated testing
- Docker and Google Cloud Run will be added as the deployment stage

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Run tests

```bash
pytest -q
```

The test suite covers the health endpoint, authentication, expense creation, listing, update, deletion, validation and 404 handling.

## Health check

Open `http://127.0.0.1:5000/health`.

Expected response:

```json
{"service":"personal-expense-tracker","status":"healthy"}
```

## Project workflow

```text
Developer -> GitHub -> CI/CD -> Docker Image -> Registry -> Cloud Run
                                             |
                                             +-> Cloud Logging / Monitoring
```

Docker, CI/CD, GCP deployment and monitoring are planned as the next implementation stage for the mini-project assignment.
