"""Database migration script to add admin fields to reservations table."""
import sqlite3
import os
from src.config.settings import get_settings

def migrate_database():
    """Add admin_decision, admin_notes, and decided_at columns to reservations table."""
    settings = get_settings()

    # Extract database path from URL
    db_path = settings.database_url.replace("sqlite:///", "")

    if not os.path.exists(db_path):
        print(f"Database not found at: {db_path}")
        return

    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(reservations)")
        columns = [col[1] for col in cursor.fetchall()]

        print(f"Existing columns: {columns}")

        # Add admin_decision column if it doesn't exist
        if "admin_decision" not in columns:
            print("Adding admin_decision column...")
            cursor.execute("ALTER TABLE reservations ADD COLUMN admin_decision TEXT")
            print("✓ admin_decision column added")
        else:
            print("admin_decision column already exists")

        # Add admin_notes column if it doesn't exist
        if "admin_notes" not in columns:
            print("Adding admin_notes column...")
            cursor.execute("ALTER TABLE reservations ADD COLUMN admin_notes TEXT")
            print("✓ admin_notes column added")
        else:
            print("admin_notes column already exists")

        # Add decided_at column if it doesn't exist
        if "decided_at" not in columns:
            print("Adding decided_at column...")
            cursor.execute("ALTER TABLE reservations ADD COLUMN decided_at TIMESTAMP")
            print("✓ decided_at column added")
        else:
            print("decided_at column already exists")

        conn.commit()
        print("\n✓ Migration completed successfully!")

        # Verify new schema
        cursor.execute("PRAGMA table_info(reservations)")
        new_columns = [col[1] for col in cursor.fetchall()]
        print(f"\nNew columns: {new_columns}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
