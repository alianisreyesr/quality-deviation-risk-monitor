# Audit Trail Specification

## Scope

`audit_log` is the operational, append-only audit-event table for this portfolio application. It supports traceability for reviewer workflow changes and mutating HTTP requests. This is a synthetic-data prototype and not a validated production electronic-record system.

## Event fields

| Field | Purpose |
|---|---|
| `id` | Immutable event identifier |
| `deviation_id` | Related deviation, when applicable |
| `action` | Domain action or HTTP method/path |
| `actor` | User or service that initiated the event |
| `created_at` | Server-generated UTC ISO-8601 timestamp |
| `previous_status`, `new_status` | Workflow-specific status transition |
| `previous_value`, `new_value` | Generic before/after values; defaults to the status fields for existing review actions |
| `reason` | Explicit business rationale; defaults to the existing `comment` value for backward-compatible callers |
| `correlation_id` | UUID grouping related events from one request or workflow; generated when a caller does not supply one |
| `comment` | Original optional reviewer note or request snapshot |
| `ip_address`, `user_agent`, `status_code`, `latency_ms` | HTTP traceability metadata |

## Compatibility and migration

At application initialization, the schema creates `audit_log` when absent and inspects existing installations with `PRAGMA table_info`. It adds only the nullable `previous_value`, `new_value`, `reason`, and `correlation_id` columns that are missing, then creates an index on `correlation_id`. Historical events are never updated, deleted, or backfilled.

## Write behavior

`insert_audit_event` remains backward compatible. For callers that provide only existing workflow fields, `previous_value` and `new_value` inherit `previous_status` and `new_status`; `reason` inherits `comment`; and a UUID `correlation_id` is generated. New callers may supply all four fields explicitly.

## Integrity rules

- Audit events are append-only; no application helper updates or deletes `audit_log` rows.
- Timestamps are generated server-side in UTC.
- The actor and action are required.
- A correlation ID supports investigation across related events without replacing the immutable event ID.
