"""
FocusBoard Automated Database Migration Runner
Safely executes Alembic migrations with connection retries and error isolation.
"""
import os
import sys
import time
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text

def run_migrations(max_retries=10, retry_delay=3):
    print("[*] Starting FocusBoard Database Migration Sequence...")
    alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "alembic.ini")
    script_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "alembic")

    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("script_location", script_dir)

    for attempt in range(1, max_retries + 1):
        try:
            print(f"[*] Attempt {attempt}/{max_retries}: Checking database connectivity and applying migrations...")
            command.upgrade(alembic_cfg, "head")
            print("[SUCCESS] All database migrations applied successfully to revision HEAD.")
            return True
        except Exception as e:
            print(f"[!] Migration attempt {attempt} failed: {e}")
            if attempt < max_retries:
                print(f"[*] Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                print("[FATAL] All migration attempts exhausted. Aborting startup.")
                return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
