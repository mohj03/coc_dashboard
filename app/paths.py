from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]   # /home/ubuntu/uguwewe
DATA_DIR  = PROJECT_ROOT / "data"
SQL_DIR   = DATA_DIR / "sql_db"
STAMP_DIR = DATA_DIR / "stamps"
CACHE_DIR = DATA_DIR / "cache_files"

for d in (SQL_DIR, STAMP_DIR, CACHE_DIR):
    d.mkdir(parents=True, exist_ok=True)

DB_PATH    = Path(os.getenv("DB_PATH") or (SQL_DIR / "cw_history.db"))
STAMP_FILE = STAMP_DIR / "CW_timestamp.txt"