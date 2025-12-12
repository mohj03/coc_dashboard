import sqlite3
from datetime import datetime, date
import time
import threading
import os
from pathlib import Path
from pprint import pprint
import json
from paths import DB, CACHE

lock = threading.Lock()
conn = sqlite3.connect(DB["cwl"], check_same_thread=False)
c = conn.cursor()

c.execute(""" CREATE TABLE IF NOT EXISTS player_cwlLog (
          tag TEXT PRIMARY KEY,
          name TEXT,
          th INTEGER,
          stars INTEGER DEFAULT 0,
          points REAL DEFAULT 0.0,
          attacks_used INTEGER DEFAULT 0,
          possible_attacks INTEGER DEFAULT 0
          )
          """)

c.execute("""
    CREATE TABLE IF NOT EXISTS player_cwlLog_log (
        tag TEXT,
        name TEXT,
        th INTEGER,
        stars INTEGER,
        points REAL,
        attacks_used INTEGER,
        possible_attacks INTEGER,
        date TEXT
    )
    """)
conn.commit()

def save_cwlInfo(data):
    with lock:
            try:
                for tag, player in data.items():
                    if tag == "war_info":
                        continue

                    name = player["name"]
                    th = player["townhallLevel"]
                    stars = int(player["totalStars"])
                    points = float(player["score"]["points"])
                    attacks_used = player["attacksUsed"]

                    c.execute("""
                        SELECT stars, points, attacks_used, possible_attacks FROM player_cwlLog WHERE tag = ?
                        """, (tag,))
                    result = c.fetchone()
                    
                    if result is None:
                        tot_stars = stars
                        tot_points = points
                        attacks_used_ = attacks_used
                        possible_attacks = 1
                    
                    else:
                         tot_stars = result[0] + stars
                         tot_points = result[1] + points
                         attacks_used_ = result[2] + attacks_used
                         possible_attacks = result[3] + 1

                    c.execute(
                        """
                            INSERT INTO player_cwlLog (tag, name, th, stars, points, attacks_used, possible_attacks)
                            VALUES(?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(tag) DO UPDATE SET
                            name = excluded.name,
                            th = excluded.th,
                            stars = excluded.stars,
                            points = excluded.points,
                            attacks_used = excluded.attacks_used,
                            possible_attacks = excluded.possible_attacks
                            """, 
                                    (tag, name, th ,tot_stars , round(tot_points, 1), attacks_used_, possible_attacks)
                                )
                conn.commit()


            except Exception as e:
                print(f"En feil oppstod under lagring til database: {e}")
                conn.rollback()

def reset_cwl():
    with lock:
        try:
            today = datetime.today().strftime("%Y-%m-%d")

            # 1. Arkiver alle rader fra player_cwlLog til player_cwlLog_log
            c.execute("""
                INSERT INTO player_cwlLog_log (tag, name, th, stars, points, attacks_used, possible_attacks, date)
                SELECT tag, name, th, stars, points, attacks_used, possible_attacks, ?
                FROM player_cwlLog
            """, (today,))

            # 2. Fjern ALLE rader fra player_cwlLog
            c.execute("DELETE FROM player_cwlLog")

            conn.commit()
            print("CWL-data er arkivert og tabellen er tømt.")

        except Exception as e:
            print(f"Feil under reset_cwl: {e}")
            conn.rollback()

def cwl_rompis():
    with lock:
        try:
            c.execute("""
                SELECT tag, name, th, stars, points, attacks_used, possible_attacks,
                (1.0*points / NULLIF(possible_attacks * 100, 0))
                AS rating
                FROM player_cwlLog
                WHERE possible_attacks >= 5
                ORDER BY rating ASC, points ASC
            """)
            result = c.fetchone()
            
            if not result:

                return None
            
            else:
                rompis = {
                    "tag": result[0],
                    "name": result[1],
                    "townhall": result[2],
                    "stars": result[3],
                    "points": result[4],
                    "attacks_used": result[5],
                    "possible_attacks": result[6]
                        }      
                return rompis

        except Exception as e:
            print(f"Feil under henting av rompis: {e}")
            return None

def print_cwl_log():
    c.execute("SELECT * FROM player_cwlLog")
    rows = c.fetchall()
    col_names = [desc[0] for desc in c.description]  # kolonnenavn

    print("Innhold i player_cwlLog:\n")
    print("\t".join(col_names))
    for row in rows:
        print(row)

if "__main__" == __name__:
    with open(CACHE["live_war"], "r", encoding="utf-8") as f:
        data = json.load(f)
    #save_cwlInfo(data)
    #reset_cwl()
    pprint(print_cwl_log())
    pprint(cwl_rompis())