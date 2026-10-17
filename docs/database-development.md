# Database Development Guide

## The Three Main Pieces

SQLAlchemy models are Python classes that describe tables, columns, relationships, and validation constraints.

Alembic migrations are ordered database changes stored in Git. A migration lets every environment move from one known schema version to the next.

A database session is the unit used by backend code to query and save data. A session should be opened for one request and always closed afterward.

## Important Files

- `backend/app/db/base.py`: shared model base and reusable ID/timestamp columns
- `backend/app/db/session.py`: PostgreSQL engine and request-scoped session
- `backend/app/models/`: WorkHub database models
- `backend/alembic/`: migration environment and version files
- `backend/alembic.ini`: Alembic configuration

## Applying Migrations

Run these commands from the repository root on the server:

```bash
docker compose exec backend alembic current
docker compose exec backend alembic upgrade head
```

`current` shows the database version. `upgrade head` applies every migration that has not yet run.

## Creating a Future Migration

After changing a SQLAlchemy model:

```bash
docker compose exec backend alembic revision --autogenerate -m "describe the change"
```

Review the generated migration before applying it. Autogeneration is useful, but it cannot understand every business intention.

Then apply and verify it:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

Commit both the model change and migration in the same Git update.

## Safe Migration Rule

Never edit a migration that has already been applied to production. Create a new migration that changes the existing schema. This keeps every server's migration history consistent.
