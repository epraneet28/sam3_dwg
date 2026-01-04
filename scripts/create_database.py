"""Create and initialize the SAM3 Drawing Segmenter database.

This script creates the SQLite database and all required tables.
Run this once during initial setup or after schema changes.

Usage:
    python scripts/create_database.py [--reset]

    --reset: Drop all existing tables and recreate (WARNING: deletes all data!)
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sam3_segmenter.database import init_db, reset_db, get_database_url


def main():
    """Create database and tables."""
    reset = "--reset" in sys.argv

    if reset:
        print("⚠️  WARNING: Resetting database - all data will be deleted!")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != "yes":
            print("Cancelled.")
            return

        print(f"Resetting database at {get_database_url()}...")
        reset_db()
        print("✅ Database reset complete!")
    else:
        print(f"Creating database at {get_database_url()}...")
        init_db()
        print("✅ Database created successfully!")

    print("\nCreated tables:")
    print("  - exemplars (stores exemplar image metadata)")
    print("  - drawings (stores uploaded drawings and segmentation results)")


if __name__ == "__main__":
    main()
