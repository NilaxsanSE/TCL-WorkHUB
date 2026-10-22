# Time Tracking Development

## Employee Workflow

1. `POST /api/time/check-in` opens a work session using a server-generated UTC timestamp.
2. `POST /api/time/breaks/start` starts one meal, rest, or other break.
3. `POST /api/time/breaks/end` closes the active break.
4. `POST /api/time/check-out` completes the session when no break is active.
5. `GET /api/time/status` returns the employee's current state and live totals.
6. `GET /api/time/sessions` returns only the authenticated employee's history.

The browser supplies its IANA timezone name for display context, but it never supplies authoritative check-in, break, or check-out timestamps.

## Administrator View

`GET /api/admin/time/sessions` returns recent sessions across all employees. An optional `user_id` query parameter filters the result to one employee.

Administrators review time records but do not use employee check-in controls.

## Enforced Rules

- one open work session per employee
- one active break per work session
- a break requires an open work session
- checkout is blocked while a break is active
- employees can read and modify only their own time records
- administrators can read all employee sessions

The duplicate-session and duplicate-break rules are protected by both API checks and partial unique PostgreSQL indexes. This protects the data when requests arrive at nearly the same time.

## Duration Calculation

Gross time is the interval from check-in to checkout, or the current server time for an open session. Worked time is gross time minus all break time. Open sessions and breaks are calculated live and are not stored as derived totals.

## Verification

```bash
docker compose run --rm --no-deps backend sh -c "pip install '.[test]' && pytest -q"
docker compose run --rm --no-deps frontend npm run build
docker compose exec backend alembic check
```
