# Quality Deviation Risk Monitor

Portfolio-safe quality deviation risk monitoring prototype built with Python, SQL, FastAPI, React, and synthetic data.

## Portfolio Safety and Intended Use

**⚠️ IMPORTANT:** This repository uses **synthetic, non-production data only**. It is a portfolio prototype, not a validated GxP system, and is not a substitute for approved procedures, validation documentation, production controls, or regulated decision-making.

See [Portfolio Safety and Intended Use](docs/PORTFOLIO_SAFETY.md) for detailed guidance.

## Focus

The project demonstrates how structured quality data can support proactive monitoring by applying documented scoring rules to open deviations and surfacing tiered risk signals for human review.

## Technology Stack

- **Backend:** Python 3.11, FastAPI, Uvicorn
- **Frontend:** React 18, Vite 5
- **Data:** CSV-based synthetic data with ALCOA+ validation
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest

## Project Structure

```
quality-deviation-risk-monitor/
├── app/                    # FastAPI backend
│   ├── main.py            # API endpoints
│   └── config.py          # Risk scoring configuration
├── frontend/              # React/Vite frontend
│   ├── src/
│   │   ├── main.jsx       # Main React component
│   │   └── styles.css     # Styling
│   ├── index.html         # HTML entry point
│   ├── package.json       # Node dependencies
│   ├── vite.config.js     # Vite configuration
│   └── Dockerfile         # Frontend container
├── data/                  # Synthetic data files
│   └── deviations.csv     # Sample deviation records
├── scripts/               # Utility scripts
│   ├── init_pipeline.sh   # Setup script
│   └── load_data.py       # Data loading with validation
├── sql/                   # Database schema (optional)
│   └── schema.sql
├── tests/                 # Unit tests
│   └── test_main.py
├── docs/                  # Documentation
│   ├── PORTFOLIO_SAFETY.md
│   ├── architecture.md
│   ├── data-dictionary.md
│   └── validation-summary.md
├── docker-compose.yml     # Multi-service orchestration
├── Dockerfile             # Backend container
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/alianisreyesr/quality-deviation-risk-monitor.git
   cd quality-deviation-risk-monitor
   ```

2. **Initialize the pipeline:**
   ```bash
   chmod +x scripts/init_pipeline.sh
   ./scripts/init_pipeline.sh
   ```
   
   Or manually:
   ```bash
   cp .env.example .env
   docker compose up --build
   ```

3. **Access the application:**
   - **Frontend:** http://localhost:3000
   - **API:** http://localhost:8000
   - **Health Check:** http://localhost:8000/health

### Local Development (without Docker)

**Backend:**
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Features

- **Risk Scoring Engine:** Automated risk calculation based on ICH Q9(R1) and ICH Q10 guidelines
- **Tiered Risk Levels:** Low, Medium, High classification with transparent scoring logic
- **Interactive Dashboard:** React-based UI for reviewing deviations
- **Filtering & Drill-down:** Filter by risk level and view detailed risk reasons
- **ALCOA+ Compliance:** Data validation principles demonstrated in load scripts
- **Containerized Deployment:** Reproducible environment with Docker Compose

## API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/health` | GET | System health status | None |
| `/deviations` | GET | List all deviations with risk scores | `risk_level` (optional: Low, Medium, High) |
| `/summary` | GET | Risk summary statistics | None |

### Example Requests

```bash
# Health check
curl http://localhost:8000/health

# All deviations
curl http://localhost:8000/deviations

# High-risk deviations only
curl "http://localhost:8000/deviations?risk_level=High"

# Summary statistics
curl http://localhost:8000/summary
```

### Example Response

```json
{
  "count": 6,
  "records": [
    {
      "deviation_id": "DEV-1001",
      "title": "Temperature excursion documentation delay",
      "severity": "High",
      "risk_score": 8,
      "risk_level": "High",
      "risk_reasons": [
        "High severity",
        "Past due date",
        "Repeat occurrence"
      ]
    }
  ]
}
```

## Risk Scoring Logic

The risk scoring algorithm applies points based on:

| Factor | Points | Regulatory Reference |
|--------|--------|---------------------|
| Severity (High) | 3 | ICH Q9(R1) §4 |
| Severity (Medium) | 1 | ICH Q9(R1) §4 |
| Past due date | 3 | ICH Q10 §3.2 |
| No investigation owner | 2 | ICH Q10 §3.2 |
| Repeat occurrence | 2 | ICH Q10 §3.2 |
| Incomplete record | 2 | 21 CFR Part 11 / EU Annex 11 |
| Open >30 days | 1 | ICH Q10 §3.2 |
| Open >60 days | +2 | ICH Q10 §3.2 |

**Risk Thresholds:**
- **High:** Score ≥ 5
- **Medium:** Score ≥ 2
- **Low:** Score < 2

## Governance Principles Demonstrated

- ✅ Synthetic-data boundary for public demonstrations
- ✅ Traceable and reviewable risk logic
- ✅ Human-in-the-loop interpretation of risk signals
- ✅ Clear separation between prototype and validated production system
- ✅ ALCOA+ data integrity principles

## Testing

Run backend tests:
```bash
pytest tests/ -v
```

## Development

### Code Style
- Python: Follow PEP 8 guidelines
- JavaScript/React: Use ESLint recommended rules

### Adding New Features
1. Create a feature branch
2. Implement changes with tests
3. Document in relevant markdown files
4. Submit pull request with validation notes

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## Documentation

- [Portfolio Safety](docs/PORTFOLIO_SAFETY.md) - Intended use and limitations
- [Architecture](docs/architecture.md) - System design overview
- [Data Dictionary](docs/data-dictionary.md) - Field definitions
- [Validation Summary](docs/validation-summary.md) - ALCOA+ compliance

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## Security

See [SECURITY.md](SECURITY.md) for responsible disclosure and repository safety guidance.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## Disclaimer

**This is a portfolio demonstration tool only.** It is not intended for:
- Production use
- Regulated decision-making
- Patient safety determinations
- Quality release decisions

Always follow your organization's approved procedures and validated systems for actual quality management activities.
