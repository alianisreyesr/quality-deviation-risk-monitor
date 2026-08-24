# Case study: explainable deviation-risk triage

## Problem

Quality teams need to identify potentially important deviation patterns without turning an opaque score into an automated quality decision.

## Users and outcome

Reviewers receive a prioritized queue, inspect the contributing rules, record triage decisions, and retain attributable history. The result is a review aid that makes prioritization explainable while keeping authority with a human reviewer.

## Engineering decisions

- Deterministic Python rules expose the reason behind each score.
- FastAPI separates scoring and workflow services from the React review experience.
- SQLite and synthetic CSV inputs make the data path reproducible and safe for a public portfolio.
- Tests cover ingestion, scoring, contracts, workflow behavior, and security-sensitive paths.

## Evidence

The project includes architecture and lineage documentation, regulatory references, automated tests, CI, containerization, and security guidance.

## Boundary

This prototype does not predict patient, product, or compliance outcomes and must not make regulated decisions. Production adoption would require validated source integrations, governed thresholds, access controls, formal assurance, monitoring, and quality-unit approval.
