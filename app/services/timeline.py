import sqlite3
from pathlib import Path
from pprint import pprint
from datetime import datetime, timezone
print("Local:", datetime.now())
print("UTC  :", datetime.now(timezone.utc))

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data/sql_db/cw_history.db"

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

def test(tag):

    c.execute("""
        SELECT
          id,
          player_tag,
          th_level,
          attack_used,
          stars,
          unfiltered_points AS points,
          destruction_percent AS destruction,
          timestamp
        FROM player_war_log
        WHERE player_tag = ?
        ORDER BY timestamp ASC
    """, (tag,))
    rows =  c.fetchall()
    datapoints = []
    for row in rows:
        tag_ = row[1]
        th = row[2]
        attacks =row[3]
        stars =row[4]
        points = row[5]
        destruction = row[6]
        timestamp = row[7]
        data = {"tag": tag_,
                "townhall": th,
                "attacks_used": attacks,
                "stars": stars,
                "points": points,
                "destruction": destruction,
                "timestamp": timestamp}
        datapoints.append(data)
    return datapoints

pprint(test("#YLY98QCU"))
