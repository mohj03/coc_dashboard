import sqlite3
import os
import shutil
import glob
from datetime import datetime
from app.paths import SQL_BACKUP

def backup_database(db_path: str, endtime: str):
    os.makedirs(SQL_BACKUP, exist_ok=True)

    # Bruk endtime som filnavn
    timestamp = endtime.replace(":", "-").replace("T", "_")
    backup_file = f"{SQL_BACKUP}/{timestamp}.db"

    # Lag trygg kopi med SQLite-backup API
    with sqlite3.connect(db_path) as src, sqlite3.connect(backup_file) as dst:
        src.backup(dst)
    print(f"Backup lagret til: {backup_file}")

def rotate_backups(keep:int=8, folder="data/sql_backup"):
    files = sorted(glob.glob(os.path.join(folder, "*.db")), key=os.path.getmtime, reverse=True)
    for f in files[keep:]:
        try: os.remove(f)
        except OSError: pass



