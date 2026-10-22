# TCL WorkHub

TCL WorkHub is an internal work-hours, verification, approval, payment, and invoice management system for Technology Center Lanka.

The system complements Zammad. Zammad remains the source for task and ticket details, while WorkHub records working time, links that time to Zammad references, supports administrator verification, calculates approved payable amounts, and prepares reports and invoices.

## First Development Goal

Build a Docker-first MVP that can run on the Debian 13 server at `10.20.11.110` after SSH access is available.

The first version will support:

- Keycloak authentication from the beginning
- employee and administrator roles
- manual Zammad ticket references
- employee check-in, check-out, and breaks
- daily and monthly timesheet views
- admin review, rejection, correction, and approval
- hourly rates with effective dates
- approved payable amount calculation
- employee-only visibility for own records
- administrator visibility across all employees
- invoice generation later using the supplied invoice format

## Planned Services

- `frontend`: Next.js and TypeScript user interface
- `backend`: FastAPI API service
- `postgres`: application database
- `keycloak`: authentication and roles
- `redis`: optional support service for future background jobs and caching

## Authentication Foundation

The first protected endpoints and browser login flow use Keycloak Authorization Code Flow with PKCE. FastAPI validates signed access tokens and synchronizes the authenticated identity to the local `users` table. See [Authentication Development](docs/authentication-development.md) for the flow and configuration model.

## Time Tracking

Employees can check in, record breaks, check out, and review their own session history. Administrators can review sessions across all employees. The API rules and duration model are documented in [Time Tracking Development](docs/time-tracking-development.md).

## Local Policy

This repository is prepared locally, but heavy Docker builds and database volumes should run on the server because local disk space is limited.

Do not commit `.env` files or generated Docker volumes.

## Server Plan

The server is reachable through OpenVPN:

- private IP: `10.20.11.110`
- SSH port: `22`
- OS: Debian 13
- public access: later through the TechCenter reverse proxy

Once SSH access is available, deployment should use `/opt/tcl-workhub` or another admin-approved directory.

