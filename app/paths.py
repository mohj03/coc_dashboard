from pathlib import Path

# Root directory
root_dir = Path("data")

# DATABASE FILES
db_dir = root_dir / "sql_db"

DB = {
    "cw": db_dir / "cw_history.db",
    "cwl": db_dir / "cwl_history.db",
}


# CACHE FILES
cache_dir = root_dir / "cache_files"

CACHE = {
    "all_monthly": cache_dir / "all_monthly.json",
    "clan_info": cache_dir / "clan_info.json",
    "clan_members": cache_dir / "clan_members.json",
    "live_war": cache_dir / "LIVE-war.json",
    "logcw": cache_dir / "LOGcw.json",
    "mvp": cache_dir / "mvp.json",
    "rompis": cache_dir / "rompis.json",
    "theme": cache_dir / "theme.json",
    "top10_month": cache_dir / "top10_month.json",
}

# BACKUP DIRECTORIES
backup_dir = root_dir / "backup"

BACKUP = {
    "root": backup_dir,
    "cw": backup_dir / "cw",
    "cwl": backup_dir / "cwl",
}

# SQL BACKUP DIRECTORY
SQL_BACKUP = root_dir / "sql_backup"

# STAMP / COUNTER FILES
stamps_dir = root_dir / "stamps"

STAMPS = {
    "cw": stamps_dir / "CW_timestamp.txt",
    "cwl": stamps_dir / "CWL_timestamp.txt",
    "cwl_season": stamps_dir / "CWL_seasonstamp.txt",
    "war_counter": stamps_dir / "war_counter.txt",
    "war_tags_cwl": stamps_dir / "war_tags_cwl.json",
}