# THIS IS INTENDED TO BE A HIGH LEVEL EXAMPLE
from sqlalchemy import text
from datetime import datetime
import shutil, os
from pathlib import Path
from .models import engine, Base  # Import from models.py

# DB setup - supports SQLite or PostgreSQL (Railway)
DB_URL = os.getenv('DATABASE_URL', 'sqlite:///app.db')

# ==============================================================================
# Database Utility Functions
# ==============================================================================

def backup_db(backup_dir="backups"):
    # For SQLite: direct file copy
    Path(backup_dir).mkdir(exist_ok=True)
    backup_path = f"{backup_dir}/app_{datetime.now().strftime('%Y%m%d_%H%M')}.db"

    # @Cursor AI: For Railway PostgreSQL, just print the URL to the Postgres service and instruct user to create a manual backup, we also dont need the `backup_dir="backups"`
    # So for example:
    # print("\n⚠️Please create a manual backup in your Railway PostgreSQL service:")
    # print("https://railway.com/project/e6...d706/service/0e...979/backups")
    # print("1. Go to Railway dashboard > 2. PostgreSQL service > Backups tab > 3. Click 'Create Backup'")
    return backup_path

def restore_db(backup_path):
    # For SQLite: overwrite DB file
    # For Railway PostgreSQL: psql with connection string
    pass  # Placeholder implementation

# TODO: maybe some function to close all open connections before a migration? not sure how aggressive to be

# ==============================================================================
# Migrations
# ==============================================================================

def migration_add_column():
    backup_db("migration_backups")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE main_table ADD COLUMN IF NOT EXISTS new_field TEXT"))
        conn.commit()

def migration_drop_legacy():
    # ⚠️ WARNING: This will permanently delete legacy tables
    backup_db("migration_backups")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS legacy_table"))
        conn.commit()

# CLI interface
if __name__ == "__main__":
    print("Available migrations:\n1. Add new_field column\n2. Drop legacy tables")
    choice = input("Select migration (1-2): ")
    if choice == "1":
        confirm = input("Add new_field column to main_table? (y/n): ")
        if confirm.lower() == "y":
            migration_add_column()
            print("Added new column")
        else:
            print("Operation cancelled")
    elif choice == "2":
        confirm = input("⚠️ WARNING: This will delete tables. Type 'DROP' to confirm: ")
        if confirm == "DROP":
            migration_drop_legacy()
            print("Dropped legacy tables")
        else:
            print("Operation cancelled")