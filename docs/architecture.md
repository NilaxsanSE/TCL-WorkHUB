# TCL WorkHub Architecture

## Product Boundary

Zammad remains the task and ticket system. WorkHub records time, connects that time to Zammad references, supports administrator verification, and calculates approved payable amounts.

Initial Zammad support is manual:

- employee or admin enters ticket number, ticket title, and ticket URL
- WorkHub stores the reference with the relevant work session or timesheet period
- administrators review the Zammad records manually before approval

Later API integration can sync ticket metadata, status, assignment, comments, and activity summaries.

## Authentication

Keycloak is required from the beginning.

Recommended realm:

- realm: `tcl-workhub`
- frontend client: `tcl-workhub-web`
- backend/API client: `tcl-workhub-api`

Recommended roles:

- `employee`
- `admin`

Visibility rules:

- employees can see only their own records, payable amounts, and invoices
- administrators can see and manage all employees, approvals, rates, payments, and invoices

## Core Workflow

1. Employee checks in.
2. Employee records breaks when needed.
3. Employee checks out.
4. Employee links relevant Zammad ticket references.
5. Employee submits a timesheet period.
6. Administrator reviews hours, Zammad references, and audit history.
7. Administrator approves, rejects, or returns for correction.
8. Approved hours become payable.
9. System calculates payable amount from approved hours and effective hourly rate.
10. Administrator marks payment status and generates invoice/report.

## Mandatory Business Rule

Recorded hours are not payable until an authorized administrator approves the relevant period.

No admin approval means no final payable amount and no final invoice.

## Deployment Shape

The first deployment should run on Debian 13 with Docker Compose:

- Next.js frontend
- FastAPI backend
- PostgreSQL database
- Keycloak authentication

The server initially listens on private network ports. Public HTTPS access should be added later through the TechCenter reverse proxy.

