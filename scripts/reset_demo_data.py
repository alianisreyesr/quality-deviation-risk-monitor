"""Reset the local Quality Deviation Risk Monitor database using synthetic source data only."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.config import DATABASE_FILE
from app.database import fetch_deviations, reset_database


def main() -> None:
    reset_database()
    print(f"Reset complete: {DATABASE_FILE}")
    print(f"Loaded {len(fetch_deviations())} synthetic deviation records.")


if __name__ == "__main__":
    main()
