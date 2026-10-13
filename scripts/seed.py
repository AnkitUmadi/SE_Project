"""Populate the database with demo data for all teammates (Issue #4).

Usage (from the SE_Project folder, with the venv active):
    python scripts/seed.py

Safe to re-run: existing records are preserved without creating duplicates.
"""

import os
import sys

# Let Python find the src package when run as "python scripts/seed.py"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=wrong-import-position
from src.app import create_app
from src.services.seed_service import DEFAULT_SEED_PASSWORD, seed_database


def main():
    """Create tables if needed and populate seed data."""
    app = create_app()
    with app.app_context():
        summary = seed_database()
        print("Database seeded successfully:")
        for key, count in summary.items():
            print(f"  - {key}: {count}")
        print(
            "\nDemo accounts (default password from SEED_DEFAULT_PASSWORD or "
            f"'{DEFAULT_SEED_PASSWORD}'):"
        )
        print("  - Admin:   admin@pes.edu")
        print("  - Faculty: faculty1@pes.edu, faculty2@pes.edu, faculty3@pes.edu")
        print("  - Student: student01@pes.edu .. student30@pes.edu")


if __name__ == "__main__":
    main()
