#!/usr/bin/env python3
"""
FocusBoard Database Backup Utility
Creates a point-in-time compressed backup of the FocusBoard database
with SHA256 integrity checksum and automated retention policy pruning.
"""
import os
import sys
import gzip
import shutil
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings

BACKUP_DIR = BASE_DIR / "backups"
MAX_RETENTION = 7  # Keep last 7 backups

def compute_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def backup_sqlite(source_path: str, backup_dir: Path) -> Path:
    """Safely snapshot SQLite database using SQLite online backup API."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_backup = backup_dir / f"focusboard_{timestamp}.db"
    compressed_backup = backup_dir / f"focusboard_{timestamp}.db.gz"
    checksum_file = backup_dir / f"focusboard_{timestamp}.db.gz.sha256"

    print(f"[*] Connecting to source database: {source_path}")
    src_conn = sqlite3.connect(source_path)
    dst_conn = sqlite3.connect(str(raw_backup))

    with dst_conn:
        src_conn.backup(dst_conn, pages=100)
    
    src_conn.close()
    dst_conn.close()

    print(f"[*] Compressing backup to: {compressed_backup.name}")
    with open(raw_backup, "rb") as f_in, gzip.open(compressed_backup, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Clean up uncompressed raw backup
    raw_backup.unlink()

    # Generate and store SHA256 checksum
    digest = compute_sha256(compressed_backup)
    with open(checksum_file, "w") as f:
        f.write(f"{digest}  {compressed_backup.name}\n")

    print(f"[+] Backup successfully generated: {compressed_backup.name} (SHA256: {digest[:12]}...)")
    return compressed_backup

def prune_old_backups(backup_dir: Path, retention: int = MAX_RETENTION):
    """Prune backups exceeding the retention threshold."""
    backups = sorted(backup_dir.glob("focusboard_*.db.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    if len(backups) > retention:
        for old in backups[retention:]:
            print(f"[*] Pruning expired backup: {old.name}")
            old.unlink(missing_ok=True)
            checksum = old.with_suffix(".gz.sha256")
            if checksum.exists():
                checksum.unlink(missing_ok=True)

def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        sqlite_file = db_url.replace("sqlite:///", "")
        if not Path(sqlite_file).is_absolute():
            sqlite_file = BASE_DIR / sqlite_file
        
        if not Path(sqlite_file).exists():
            print(f"[!] Target SQLite database does not exist: {sqlite_file}")
            sys.exit(1)

        backup_sqlite(str(sqlite_file), BACKUP_DIR)
        prune_old_backups(BACKUP_DIR)
    else:
        print(f"[!] PostgreSQL backup requires pg_dump utility. URL: {db_url}")

if __name__ == "__main__":
    main()
