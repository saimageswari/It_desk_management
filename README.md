# IT Helpdesk Ticket Management System

A role based support ticket application built with Streamlit, SQLAlchemy, and MySQL. Employees create and track requests, support agents manage assigned work, and administrators manage accounts, assignments, categories, and analytics.

## Features

- Employee self registration, bcrypt password storage, login, and account activation checks.
- Role enforced in service functions for ticket access, status changes, assignment, and account administration.
- Ticket categories, priorities, valid status transitions, ticket numbers, assignment, comments, history, and notifications.
- Role dashboards, ticket search and filters, Plotly analytics, and CSV export.
- SQLAlchemy relationships and constraints, Alembic migration setup, environment based database configuration, and pytest coverage.

## Requirements

Python 3.11 or newer is recommended. MySQL 8+ is recommended for deployment. SQLite is used by default for local development when `DATABASE_URL` is not set.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `DATABASE_URL` in `.env`. For MySQL, create the database and a least privilege application account:

```sql
CREATE DATABASE helpdesk_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'helpdesk'@'%' IDENTIFIED BY 'use-a-long-unique-secret';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES ON helpdesk_db.* TO 'helpdesk'@'%';
```

Set `BOOTSTRAP_ADMIN_NAME`, `BOOTSTRAP_ADMIN_EMAIL`, and a strong `BOOTSTRAP_ADMIN_PASSWORD` in `.env`, then initialize the schema, categories, and initial administrator:

```bash
python -m database.seed
```

The bootstrap command refuses to create a second administrator. Remove the bootstrap password from `.env` after initial setup. The Streamlit app never offers public administrator registration.

Run the app:

```bash
streamlit run app.py

```

## Schema migrations

The first Alembic revision establishes the schema. Use migrations for deployed databases:

```bash
alembic upgrade head
```

The current app also calls SQLAlchemy `create_all` during startup for first-run convenience. For managed production environments, run Alembic as a release step and restrict DDL privileges from the normal app account after initialization.

## Tests

Tests use a fresh in-memory SQLite database and do not connect to the configured database:

```bash
pytest -q
```

## Streamlit deployment

Deploy this repository as a Streamlit application with `streamlit run app.py` and install from `requirements.txt`. Configure `DATABASE_URL` and bootstrap values using the platform's encrypted secrets/environment settings. Use a hosted MySQL service reachable from the app, configure TLS and network allowlisting, and do not assume a developer's local MySQL server can be reached by a cloud host. Provision backups and apply migrations before starting a new release. Set `APP_ENV=production` in hosted environments.

## Project map

- `app.py`: Streamlit views and navigation.
- `database/`: ORM models, connection/session setup, initial seed, and SQL note.
- `services/`: authentication, authorization, ticket, comment, notification, and user workflows.
- `repositories/`: reusable read query helpers.
- `migrations/`: Alembic environment and initial schema revision.
- `tests/`: isolated service and permission tests.

## Security and operational notes

Passwords are bcrypt hashed. Registration always creates an Employee account. Account activation and role permissions are checked on the server side in service entry points. Ticket creation, assignment, status changes, and comments write audit history in the same database transaction. Use a private, TLS protected MySQL connection and unique secrets in production. Uploaded files are not enabled in this release.


## demo live

https://itdeskmanagement-kjrztgba7xopypulgudtql.streamlit.app/

