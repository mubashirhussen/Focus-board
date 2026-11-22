#!/usr/bin/env python3
"""
FocusBoard Disaster Recovery / Database Restoration Utility
Restores database from a compressed backup archive after verifying SHA256 checksum.
"""
import os
import sys
import gzip
import shutil
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings

def compute_sha256(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def restore_sqlite(archive_path: Path, target_path: Path):
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive not found: {archive_path}")

    # Check checksum if available
    checksum_file = archive_path.with_name(archive_path.name + ".sha256")
    if checksum_file.exists():
        expected_digest = checksum_file.read_text().split()[0].strip()
        actual_digest = compute_sha256(archive_path)
        if expected_digest.lower() != actual_digest.lower():
            raise ValueError(f"Checksum mismatch! Expected: {expected_digest}, Got: {actual_digest}")
        print("[+] Checksum verified successfully.")

    # Create safety snapshot of existing target DB
    if target_path.exists():
        safety_copy = target_path.with_suffix(f".pre_restore_safety_{os.getpid()}")
        shutil.copy2(target_path, safety_copy)
        print(f"[*] Pre-restore safety copy created at: {safety_copy.name}")

    # Decompress to temporary file then atomically replace
    temp_restored = target_path.with_suffix(".restoring_tmp")
    with gzip.open(archive_path, "rb") as f_in, open(temp_restored, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    temp_restored.replace(target_path)
    print(f"[+] Successfully restored database to: {target_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python restore_db.py <path_to_backup.db.gz>")
        sys.exit(1)

    archive = Path(sys.argv[1])
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        sqlite_file = db_url.replace("sqlite:///", "")
        if not Path(sqlite_file).is_absolute():
            sqlite_file = BASE_DIR / sqlite_file
        restore_sqlite(archive, Path(sqlite_file))
    else:
        print(f"[!] PostgreSQL restore requires psql utility. URL: {db_url}")

if __name__ == "__main__":
    main()
