from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT_DIR / "data" / "deviations.csv"
DATABASE_FILE = ROOT_DIR / "data" / "quality_monitor.db"
SCHEMA_FILE = ROOT_DIR / "sql" / "schema.sql"
