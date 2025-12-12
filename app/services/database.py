import sqlite3
from app.services import stats
from datetime import datetime, date
import threading
import json
from  app.services.helpers import endTime_conv
import calendar
from pathlib import Path
from pprint import pprint
from app.services.live_cwl import LiveCWL
from paths import DB, CACHE, STAMPS, root_dir

lock = threading.Lock()
conn = sqlite3.connect(DB["cw"], check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS player_cwlog (
    tag TEXT PRIMARY KEY,
    name TEXT,
    th INTEGER,

    sum_stars INTEGER DEFAULT 0,
    star_points REAL DEFAULT 0.0,
    avrg_stars REAL DEFAULT 0.0,
    avrg_attacks_used REAL DEFAULT 0.0,

    sum_attacks_used INTEGER DEFAULT 0,
    possible_attacks INTEGER DEFAULT 0,

    sum_points REAL DEFAULT 0.0,
    wars_attended INTEGER DEFAULT 0,
    rating INTEGER DEFAULT 0,
    new INTEGER DEFAULT 1
    )
    """)

c.execute("""CREATE TABLE IF NOT EXISTS player_motnhly_awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL,
    award_type TEXT NOT NULL,
    month TEXT NOT NULL, 
    speech TEXT NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

c.execute("""CREATE TABLE IF NOT EXISTS player_war_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_tag TEXT NOT NULL,
        th_level INTEGER,
        attack_used INTEGER DEFAULT 0,
        stars INTEGER DEFAULT 0,
        unfiltered_points REAL DEFAULT 0.0,
        destruction_percent REAL DEFAULT 0.0,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
         """)

c.execute(""" CREATE TABLE IF NOT EXISTS cw_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          tag TEXT,
          opp_name TEXT,
          endTime INTEGER,
          badge_url TEXT,
          vinner TEXT,
          uguw_stjerner INTEGER,
          opp_stjerner INTEGER
          )
          """)

c.execute(""" CREATE TABLE IF NOT EXISTS clan (
          name TEXT PRIMARY KEY,
          cw_won INTEGER DEFAULT 0,
          cw_lost INTEGER DEFAULT 0,
          cw_count INTEGER DEFAULT 0,
          cw_win_precent REAL DEFAULT 0
          )
          """)

c.execute(""" CREATE TABLE IF NOT EXISTS monthly (
    tag TEXT PRIMARY KEY,
    name TEXT,

    monthly_points REAL DEFAULT 0.0,
    monthly_bonus REAL DEFAULT 0.0,
    final_monthly_points REAL DEFAULT 0.0,
    precent TEXT,

    monthly_possible_bonus REAL DEFAULT 0.0,
    monthly_max_points REAL DEFAULT 0.0,

    monthly_attacks_used INTEGER DEFAULT 0,
    monthly_possible_wars INTEGER DEFAULT 0,
    monthly_possible_attacks INTEGER DEFAULT 0,

    monthly_stars INTEGER DEFAULT 0,
    cw_stars INTEGER DEFAULT 0,
    cwl_stars INTEGER DEFAULT 0,

    star_points INTEGER DEFAULT 0,

    ranked_stars INTEGER DEFAULT 0,
    ranked_cwl_stars INTEGER DEFAULT 0,

    rating INTEGER DEFAULT 0
    )
    """
        )

c.execute("""CREATE TABLE IF NOT EXISTS monthly_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          tag TEXT,
          name TEXT,
          monthly_points REAL DEFAULT 0.0,
          monthly_bonus REAL DEFAULT 0.0,
          final_monthly_points REAL DEFAULT 0.0,
          precent TEXT,
          monthly_possible_bonus REAL DEFAULT 0.0,
          monthly_max_points REAL DEFAULT 0.0,
          monthly_attacks_used INTEGER DEFAULT 0,
          monthly_possible_wars INTEGER DEFAULT 0,
          monthly_stars INTEGER DEFAULT 0,
          rating INTEGER DEFAULT 0,
          date TEXT
          )
          """)

def save_warInfo(data, scale, save=False):
    
    with lock:
        try:
            with open(STAMPS["war_counter"], "r") as f:
                all_wars = int(f.read().strip())
                max_points = round(((all_wars + 1) * 95 ), 1) #+1 fordi krigen legges på etter den har gått igjennom her
                star_value = round(max_points / 3, 1)
                if star_value == 0:
                    star_value = 1

        except ValueError:
            star_value = 1

        timestamp = data.get("war_info", {}).get("endTime", "")
        war_type = data.get("war_info", {}).get("warType", "")
        try:
            if data["war_info"]["state"] == "warEnded" or save:
                c.execute("SELECT endTime FROM cw_log ORDER BY endTime DESC LIMIT 17")
                for tag, player in data.items():
            
                    if war_type == "cw":
                        if tag == "war_info":
                            continue

                        star_points = float(player["score"]["starPoints"])
                        max_points = float(player["score"]["maxPoints"])
                        mulig_bonus = float(player["score"]["potentialBonus"])
                    
                    else:
                        if tag == "war_info":
                            continue

                        star_points = 0
                        max_points = 0
                        mulig_bonus = 0

                    name = player["name"]
                    th = player["townhallLevel"]
                    stars = float(player["totalStars"])
                    attack_used = float(player["attacksUsed"])
                    points = float(player["score"]["points"])
                    unfiltered_points = float(player["score"]["unfilteredPoints"])
                    total_destruction = float(player["totalDestruction"])
                    wars_attended = 1

                    if war_type == "cwl":
                        possible_attacks_this_war = 1

                    else:
                        possible_attacks_this_war = 2
                    
                    if scale == 0:
                        scale = 1
                
                    if war_type == "cwl":
                        points /= scale

                    #VodkaRedbull - bonus
                    

                    calc = stats.PlayerStat(tag, th, attack_used, stars, star_points, points, max_points, mulig_bonus, war_type, c)
                    avrg_stars, avrg_attacks_used, rating, sum_points, new = (calc.tuple())

                    sum_points_ = round(sum_points,1)
                    avrg_stars_ = round(avrg_stars, 1)
                    avrg_attacks_used_ = round(avrg_attacks_used, 1)

                    c.execute(
                        """
                            INSERT INTO player_cwlog (tag, name, th, sum_stars, star_points, avrg_stars, avrg_attacks_used, sum_attacks_used,
                            sum_points, wars_attended, rating, new, possible_attacks)
                            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(tag) DO UPDATE SET
                            name = excluded.name,
                            th = excluded.th,
                            sum_stars = player_cwlog.sum_stars + excluded.sum_stars,
                            star_points = excluded.star_points,
                            avrg_stars = excluded.avrg_stars,
                            avrg_attacks_used = excluded.avrg_attacks_used,
                            sum_attacks_used = player_cwlog.sum_attacks_used + excluded.sum_attacks_used,
                            sum_points = excluded.sum_points,
                            wars_attended = player_cwlog.wars_attended + excluded.wars_attended,
                            rating = excluded.rating,
                            new = excluded.new,
                            possible_attacks = player_cwlog.possible_attacks + excluded.possible_attacks
                            """, 
                                    (tag, name, th ,stars , star_points, avrg_stars_, avrg_attacks_used_, attack_used, sum_points_,
                                        wars_attended, rating, new, possible_attacks_this_war)
                                )
                
                    if war_type == "cwl":
                        points *= scale
                        cwl_stars = stars
                    else:
                        cwl_stars = 0

                    c.execute("SELECT rating FROM player_cwlog WHERE tag = ?", (tag,))
                    row = c.fetchone()
                    rating = row[0] if row else 0

                    c.execute("""
                        SELECT monthly_points, monthly_possible_bonus, monthly_attacks_used, monthly_possible_wars, 
                            monthly_possible_attacks, monthly_stars, cw_stars
                        FROM monthly WHERE tag = ?
                    """, (tag,))
                    result = c.fetchone()
                    if result is None:
                        result = (0, 0, 0, 0, 0, 0)
                        monthly_max_points = max_points

                    points_total = result[0] + points
                    possible_bonus_total = round(result[1] + mulig_bonus,1)
                    attacks_total = result[2] + attack_used
                    monthly_possible_attacks = result[4] + possible_attacks_this_war
                    monthly_possible_wars = result[3] + 1
                    monthly_stars = result[5] + stars


                    if attacks_total == 0 or monthly_possible_wars == 0 or monthly_possible_attacks == 0:
                        final_monthly_points = 0
                        points_ = 0
                        mulig_bonus_ = 0
                        monthly_max_points = 0
                        precent = "-"
                        monthly_bonus = 0
                        cw_stars = 0.0
                        cwl_stars = 0
                        ranked_stars = 0.0
                        ranked_cwl_stars = 0.0

                    else:
                        monthly_max_points = round(result[0] + points + result[1] + mulig_bonus, 1)
                        mulig_bonus_ = round(result[1] + mulig_bonus, 1)
                        points_ = round(result[0] + points, 1)
                        monthly_bonus = round(possible_bonus_total * (attacks_total / (monthly_possible_attacks)), 1)

                        if monthly_bonus == 0:
                            precent = "100%"
                        
                        elif monthly_bonus == 0 and attacks_total == 0:
                            precent = "-"

                        else:
                            precent = round(((attacks_total / monthly_possible_attacks) * 100), 1)

                        final_monthly_points = round((possible_bonus_total * (attacks_total / (monthly_possible_attacks))) + points_total, 1)

                        if war_type == "cw":

                            if attacks_total > 0 and final_monthly_points > 0:
                                cw_stars = round(final_monthly_points / star_value, 1)

                            else:
                                cw_stars = 0

                        else:
                            cw_stars = result[6]

                        ranked_stars = round(final_monthly_points / star_value, 1)
                        ranked_cwl_stars = round(ranked_stars - cw_stars, 1)

                    c.execute("""
                        INSERT INTO monthly (
                            tag, name, monthly_points, monthly_bonus, final_monthly_points, precent, monthly_possible_bonus,
                            monthly_max_points, monthly_attacks_used, monthly_possible_wars, monthly_possible_attacks, monthly_stars, rating, cw_stars, cwl_stars, star_points,
                            ranked_stars, ranked_cwl_stars
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(tag) DO UPDATE SET
                            name = excluded.name,
                            monthly_points = excluded.monthly_points,
                            monthly_bonus = excluded.monthly_bonus,
                            final_monthly_points = excluded.final_monthly_points,
                            precent = excluded.precent,
                            monthly_possible_bonus = excluded.monthly_possible_bonus,
                            monthly_max_points = excluded.monthly_max_points,
                            monthly_attacks_used = excluded.monthly_attacks_used,
                            monthly_possible_wars = excluded.monthly_possible_wars,
                            monthly_possible_attacks = monthly.monthly_possible_attacks + excluded.monthly_possible_attacks,
                            monthly_stars = excluded.monthly_stars, 
                            rating = excluded.rating,
                            cw_stars = excluded.cw_stars,
                            cwl_stars = monthly.cwl_stars + excluded.cwl_stars,
                            star_points = excluded.cw_stars + (monthly.cwl_stars + excluded.cwl_stars),
                            ranked_stars = excluded.ranked_stars,
                            ranked_cwl_stars = excluded.ranked_cwl_stars
                        
                    """, 
                    (
                        tag, name, points_, monthly_bonus, final_monthly_points, f"{precent}%", mulig_bonus_, monthly_max_points,
                        attacks_total, monthly_possible_wars, possible_attacks_this_war, monthly_stars, rating, cw_stars, cwl_stars, (cw_stars + cwl_stars), ranked_stars, ranked_cwl_stars)
                        )

                    c.execute("""
                        INSERT INTO player_war_log 
                            (player_tag, th_level, attack_used, stars, unfiltered_points, destruction_percent)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        tag,
                        th,
                        attack_used,
                        stars,
                        unfiltered_points,
                        total_destruction,
                    ))
            
            conn.commit()
            print("lagret i databasen!")
            player_cwlog_cache()

        except Exception as e:
            print(f"En feil oppstod under lagring til database: {e}")

            try:
                DIR = root_dir / "backup" / f"{war_type}" / f"{timestamp}.json"
                with open(DIR, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                print(f"backup lagret under data/backup/{war_type}/{timestamp}.json")

            except Exception as e:
                print(f"kunne ikke lagre backup: {e}")

            conn.rollback()

def player_cwlog_cache():

        c.execute("SELECT * FROM player_cwlog")
        rows = c.fetchall()

        col_names = [description[0] for description in c.description]

        player_cwlog = {}
        for row in rows:
            row_dict = dict(zip(col_names, row))
            tag = row_dict.pop("tag") 
            player_cwlog[tag] = row_dict

        cw_playerlog = json.dumps(player_cwlog, indent=2)
        return cw_playerlog

def monthly_cache():
    c.execute("SELECT * FROM monthly")
    rows_ = c.fetchall()
    col_names_ = [description[0] for description in c.description]

    result = {}
    for row in rows_:
        row_dict = dict(zip(col_names_, row))
        tag = row_dict.pop("tag")
        result[tag] = row_dict

    # Sorter result basert på poeng
    sorted_items = sorted(result.items(), key=lambda x: x[1]['final_monthly_points'], reverse=True)

    # Legg til rank
    ranked_result = {}
    for i, (tag, data) in enumerate(sorted_items):
        data["rank"] = i + 1
        ranked_result[tag] = data

    return ranked_result

def save_warLog(data):
    with lock:
        try:
            tag = data["opponent"]["tag"]
            opp_name = data["opponent"]["name"]
            endTime = data["opponent"]["endTime"]
            badge_url = data["opponent"]["badge_url"]
            vinner = data["score"]["winner"]
            uguw_stjerner = data["score"]["uguwewewewughoa_stars"]
            opp_stjerner = data["score"]["opp_stars"]

            c.execute("""INSERT INTO cw_log (tag, opp_name, endTime, badge_url, vinner, uguw_stjerner, opp_stjerner)
                        VALUES(?, ?, ?, ?, ?, ?, ?)
                    """, 
                                (tag, opp_name, endTime, badge_url, vinner, uguw_stjerner, opp_stjerner)
                    )

            name = "uguwewewewughoa"
            if vinner == "uguwewewewughoa":
                cw_won = 1
            else:
                cw_won = 0

            if vinner != "uguwewewewughoa":
                cw_lost = 1
            else:
                cw_lost = 0    

            c.execute("SELECT cw_won, cw_lost, cw_count FROM clan WHERE name = ?", (name,))
            result = c.fetchone()

            if result:
                cw_count = result[2] + 1
                total_won = result[0] + cw_won
                total_lost = result[1] + cw_lost
                cw_win_precent = round(100.0 * total_won / cw_count, 1)
            else:
                cw_count = 1
                total_won = cw_won
                total_lost = cw_lost
                cw_win_precent = 100.0 if cw_won == 1 else 0


            c.execute("""
                INSERT INTO clan (name, cw_won, cw_lost, cw_count, cw_win_precent)
                VALUES(?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    cw_won = clan.cw_won + excluded.cw_won,
                    cw_lost = clan.cw_lost + excluded.cw_lost,
                    cw_count = excluded.cw_count,
                    cw_win_precent = excluded.cw_win_precent
                    """, (name, cw_won, cw_lost,cw_count, cw_win_precent))
            

            conn.commit()

        except Exception as e:
            print(f"En feil oppstod under lagring til database: {e}")
            conn.rollback()

def monthly_score():
    with lock:
        date = datetime.today().strftime("%Y-%m-%d")

        c.execute("SELECT * FROM monthly")
        rows = c.fetchall()
        col_names = [desc[0] for desc in c.description]

        for row in rows:
            row_dict = dict(zip(col_names, row))
            c.execute("""
                INSERT INTO monthly_log (
                    tag, name, monthly_points, monthly_bonus, final_monthly_points, precent,
                    monthly_possible_bonus, monthly_max_points, monthly_attacks_used,
                    monthly_possible_wars, monthly_stars, rating, date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row_dict['tag'],
                row_dict['name'],
                row_dict['monthly_points'],
                row_dict['monthly_bonus'],
                row_dict['final_monthly_points'],
                row_dict['precent'],
                row_dict['monthly_possible_bonus'],
                row_dict['monthly_max_points'],
                row_dict['monthly_attacks_used'],
                row_dict['monthly_possible_wars'],
                row_dict["monthly_stars"],
                row_dict['rating'],
                date
            ))


            c.execute("""
                UPDATE player_cwlog
                SET
                    sum_points = sum_points + ?
                WHERE tag = ?
            """, (row_dict['monthly_bonus'], row_dict['tag']))


        c.execute("""
            UPDATE monthly SET
                monthly_points = 0.0,
                monthly_bonus = 0.0,
                final_monthly_points = 0.0,
                precent = '0%',
                monthly_possible_bonus = 0.0,
                monthly_max_points = 0.0,
                monthly_attacks_used = 0,
                monthly_possible_wars = 0,
                monthly_possible_attacks = 0,
                monthly_stars = 0,
                rating = 0
        """)

        conn.commit()

def war_count():
    count = 0
    c.execute("""
        SELECT * FROM cw_log
        ORDER BY endTime DESC
        LIMIT ?
    """, (16,))
    year = datetime.now().year
    month = datetime.now().month

    if month == 1:
        month = 12
        year = year - 1

    else:
        month = month - 1

    for row in c.fetchall():
        time = endTime_conv(row[3])
        if time[0] == year and time[1] == month:
            count += 1

        else:
            break

    count += 7 #legge til cwl kriger

    return count

def update_mvp_and_rompis(tag, award_type, month, text):
    with lock:
        c.execute("""
        INSERT INTO player_motnhly_awards (tag, award_type, month, speech)
        VALUES (?, ?, ?, ?)
        """, (tag, award_type, month, text))

        return f"{award_type} lagret for {tag} for {month}"

def clan_list(data):
    members = {}
    for player in data["items"]:
        tag = player["tag"]
        townhall = player["townHallLevel"]
        trophies = player["trophies"]
        name = player["name"]
        role = player["role"]
        icon_url = player["league"]["iconUrls"]["small"]

        c.execute(
            "SELECT rating, th, sum_stars FROM player_cwlog WHERE tag = ?",
            (tag,)
        )
        row = c.fetchone()

        if row:
            rating, th, sum_stars = row

        else:
            if townhall == 17:
                rating = 80
            elif townhall == 16:
                rating = 76
            elif townhall == 15:
                rating = 71
            elif townhall == 14:
                rating = 66
            else:
                rating = int(round(((townhall / 17) * 91) - 8))
            
            th, sum_stars = townhall, 0

        members[tag] = {
            "name": name,
            "rating": rating,
            "townhall": th,
            "role": role,
            "trophies": trophies, 
            "icon_url": icon_url,
            "sum_stars": sum_stars
        }
    return members

def update_th_stats():
    n = 40
    a = 0.05
    baseline = 2.3

    c.execute("""
        SELECT th_level, attack_used, stars, unfiltered_points
        FROM (
            SELECT id, th_level, attack_used, stars, unfiltered_points,
                   ROW_NUMBER() OVER (PARTITION BY th_level ORDER BY id DESC) AS rn
            FROM player_war_log
        )
        WHERE rn <= 40
        ORDER BY th_level, id DESC
    """)

    rows = c.fetchall()
    ema_mean = {}
    for th_level, attack_used, stars, points in rows:
        if attack_used == 0:
            continue
        ema_mean = update_ema(th_level, attack_used, stars, points, ema_mean, a)

    return ema_mean
    

def update_ema(th_level, attack_used, stars, points, ema_mean, a):
    xt = stars / attack_used
    prev_ema = ema_mean.get(th_level, {}).get("ema")
    len = ema_mean.get(th_level, {}).get("len", 0) + 1

    if prev_ema is None:
        ema_t = xt  
        norm = ema_t / 3
    else:
        ema_t = a * xt + (1 - a) * prev_ema
        norm = ema_t / 3

    ema_mean[th_level] = {"ema": round(ema_t, 3), 
                          "norm": round(norm, 3),
                          "len": len
                          }

    return ema_mean

def print_():
    c.execute("SELECT * FROM monthly")
    rows = c.fetchall()
    col_names = [desc[0] for desc in c.description]  # kolonnenavn

    print("Innhold i monthly:\n")
    print("\t".join(col_names))
    for row in rows:
        print(row)
    

if __name__ == "__main__":
    with open(CACHE["live_war"], "r", encoding="utf-8") as f:
        data = json.load(f)
    #save_warInfo(data, 1.5)
    save_warInfo(data, 1, True)
    pprint(print_())


