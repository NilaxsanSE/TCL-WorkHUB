# Initial Data Model

This is the first database model plan. It should be refined during backend implementation and converted into SQLAlchemy models and Alembic migrations.

## users

Application user profile linked to Keycloak identity.

- id
- keycloak_subject
- email
- display_name
- role
- active
- created_at
- updated_at

## work_sessions

One employee work session for a day or shift.

- id
- user_id
- started_at
- ended_at
- status
- source_timezone
- notes
- created_at
- updated_at

## work_breaks

Breaks inside a work session.

- id
- work_session_id
- started_at
- ended_at
- break_type
- notes

## zammad_references

Manual Zammad references connected to sessions or timesheet periods.

- id
- user_id
- work_session_id
- timesheet_period_id
- ticket_number
- ticket_title
- ticket_url
- work_summary
- created_at

## off_days

Approved individual or company non-working days.

- id
- user_id
- date
- off_day_type
- approval_status
- approved_by_user_id
- approved_at
- notes

## timesheet_periods

Submission and approval unit, normally monthly.

- id
- user_id
- period_start
- period_end
- status
- submitted_at
- approved_at
- approved_by_user_id
- rejection_reason
- created_at
- updated_at

## approval_records

Audit-friendly history of approval decisions.

- id
- timesheet_period_id
- admin_user_id
- decision
- reason
- created_at

## hourly_rates

Employee hourly rate history.

- id
- user_id
- rate_amount
- currency
- effective_from
- effective_to
- created_by_user_id
- created_at

## payment_records

Calculated payable amount for an approved period.

- id
- timesheet_period_id
- user_id
- approved_minutes
- rate_amount
- currency
- payable_amount
- status
- marked_paid_by_user_id
- marked_paid_at
- created_at

## invoices

Invoice metadata generated from approved payment records.

- id
- payment_record_id
- invoice_number
- invoice_status
- invoice_format
- generated_at
- generated_by_user_id
- file_path

## audit_logs

Immutable record of important system actions.

- id
- actor_user_id
- action
- entity_type
- entity_id
- before_data
- after_data
- created_at

