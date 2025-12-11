from pathlib import Path

root_dir = Path("data")

#sql database
db_dir = root_dir / "sql_db"
cw_db_dir = db_dir / "cw_history.db"
cwl_db_dir = db_dir / "cwl_history.db"


cache_dir = root_dir / "cache_files"
