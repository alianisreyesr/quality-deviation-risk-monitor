# Quality Deviation Risk Monitor

Portfolio-safe quality deviation risk monitoring prototype built with Python, SQL, FastAPI, and synthetic data.

## Portfolio safety

This repository uses **synthetic, non-production data only**. It is a portfolio prototype, not a validated GxP system, and is not a substitute for approved procedures, validation documentation, production controls, or regulated decision-making. See [Portfolio Safety and Intended Use](docs/PORTFOLIO_SAFETY.md).

## Focus

The project demonstrates how structured quality data can support proactive monitoring by applying documented scoring rules to open deviations and surfacing tiered risk signals for human review.

## Technology

- Python and FastAPI
- SQL-based data access
- Containerized local development with Docker
- Synthetic demonstration data

## Local setup

```bash
git clone https://github.com/alianisreyesr/quality-deviation-risk-monitor.git
cd quality-deviation-risk-monitor
docker compose up --build
```

Review the project files and environment configuration before running locally. Never use production, proprietary, personal, or regulated records.

## Governance principles demonstrated

- Synthetic-data boundary for public demonstrations
- Traceable and reviewable risk logic
- Human-in-the-loop interpretation of risk signals
- Clear separation between a prototype and a validated production system

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Use the issue and pull-request templates to document validation, data safety, and governance considerations.

## Security

See [SECURITY.md](SECURITY.md) for responsible disclosure and repository safety guidance.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
