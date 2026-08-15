# Contributing

Thank you for improving this portfolio prototype. Keep every contribution aligned with its synthetic-data and non-production boundaries.

## Before you contribute

- Do not commit personal, patient, manufacturing, batch, client, employer, or proprietary data.
- Do not add credentials, API keys, tokens, `.env` files, or connection strings.
- Do not represent the project as validated or compliant for production GxP use.
- Keep risk logic explainable and add or update tests when its behavior changes.

## Workflow

1. Create a focused branch from `main`.
2. Make a small, reviewable change.
3. Run `pytest -q` for API and logic changes.
4. Update documentation when behavior, scope, or fields change.
5. Open a pull request explaining purpose, verification performed, and any limitations.

## Pull request checklist

- [ ] No sensitive or real-world regulated data included
- [ ] No secrets included
- [ ] Tests pass locally
- [ ] Relevant documentation updated
- [ ] Risk or compliance boundary remains accurate

## Reporting issues

Use the repository issue template and avoid sharing confidential information.
