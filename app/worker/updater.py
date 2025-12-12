from app.services import get_cw_data
import time
from datetime import datetime, timedelta, timezone
from app.services import backup
import json
from app.paths import CACHE, STAMPS, BACKUP, DB

def cw_loop():
    theme = {
        "theme": "noWar",
        "warInfo": None
    }

    while True:

        count = 60
        try:
            get_cw_data.get_clan_mebers()
            today = datetime.now().day
            month = datetime.now().month
            LOGcw_player_cache = get_cw_data.fetch_from_LIVEcw()


            if LOGcw_player_cache:
                state =  LOGcw_player_cache[0].get("war_info", {}).get("state", "")

                if state != "warEnded":
                    get_cw_data.fetch_from_monthly()
                
                if state in ("preparation", "inWar"):
                    with open(CACHE["theme"], "w", encoding="utf-8") as f:
                        json.dump(LOGcw_player_cache[1], f, indent=2, ensure_ascii=False)

                else:
                    with open(CACHE["theme"], "w", encoding="utf-8") as f:
                        json.dump(theme, f, indent=2, ensure_ascii=False)

                if state == "preparation":
                    count = 10
                
                elif state == "inWar":
                    count = 5

                elif state == "warEnded":
                    endtime = LOGcw_player_cache[0]["war_info"]["endTime"]
                    count = 60

                    try:
                        with open(STAMPS["cw"], "r") as f:
                            timestamp = f.read().strip()

                    except FileNotFoundError:
                        timestamp = ""

                    if endtime != timestamp or not timestamp:
                        print("lagrer krig!")

                        count = 60

                        get_cw_data.fetch_from_LIVEmonthly(LOGcw_player_cache[0])
                        get_cw_data.fetch_from_monthly()

                        LOGcw_clan_cache = get_cw_data.fetch_from_LOGcw()
                        get_cw_data.save_LOGcw(LOGcw_clan_cache)

                        top10_monthly_data = get_cw_data.data_from_monthly()
                        get_cw_data.fetch_from_top10(top10_monthly_data)

                        try:
                            backup.backup_database(DB["cw"], endtime=endtime)
                            backup.rotate_backups()

                        except Exception as e:
                            print(f"ingen backup: {e}")

                        get_cw_data.get_clan_mebers()

                        try:
                            with open(STAMPS["war_counter"], "r") as f:
                                war_counter = int(f.read().strip())

                        except (FileNotFoundError, ValueError):
                            war_counter = 0

                        war_counter += 1

                        with open(STAMPS["war_counter"], "w") as f:
                            f.write(str(war_counter))

                        print("alt lagret")

                        with open(STAMPS["cw"], "w") as f:
                            f.write(endtime)
                            
                        print("timestamp endret")

            elif today < 12:
                try:
                    with open(STAMPS["cwl_season"], "r") as f:
                        seasonstamp = f.read()

                except FileNotFoundError:
                    seasonstamp = ""
                    
                count = 60

                if today <= 4 or seasonstamp == "inWar":
                    season = get_cw_data.cwl_check()
                    if not season:

                        with open(CACHE["theme"], "w", encoding="utf-8") as f:
                            json.dump(theme, f, indent=2, ensure_ascii=False)

                    if today == 4 and not season:
                        if seasonstamp != f"noWar, {month}":
                            top10_monthly_data = get_cw_data.data_from_monthly()
                            top10_monthly = get_cw_data.fetch_from_top10(top10_monthly_data)

                            get_cw_data.fetch_from_mvp(top10_monthly[1])
                            get_cw_data.fetch_from_rompis(top10_monthly[2], None)

                            get_cw_data.reset_cwl()
                            get_cw_data.save_mothly()

                            with open(STAMPS["war_counter"], "w") as f:
                                f.write(str(0))

                            future = datetime.now(timezone.utc) + timedelta(days=2)
                            future_str = future.strftime("%Y%m%dT%H%M%S.000Z")
                            theme_ = {
                                "theme": "top10",
                                "warInfo": {
                                    "endTime": future_str
                                }
                            }

                            with open(CACHE["theme"], "w", encoding="utf-8") as f:
                                json.dump(theme_, f, indent=2, ensure_ascii=False)

                            print("alt lagret, ingen krig!")
                            count = 5

                            with open(STAMPS["cwl_season"], "w") as f:
                                f.write(f"noWar, {month}")

                    if season:
                        count = 5
                        
                        with open(STAMPS["cwl_season"], "w") as f:
                            f.write("inWar")

                        LOGcwl_player_cache = get_cw_data.get_cwl()

                        if not LOGcwl_player_cache:
                            print("feil i get_cwl()")
                            
                        
                        update = LOGcwl_player_cache[2]
                        last_war = LOGcwl_player_cache[3]

                        if LOGcwl_player_cache[2]:

                            with open(CACHE["theme"], "w", encoding="utf-8") as f:
                                json.dump(LOGcwl_player_cache[1], f, indent=2, ensure_ascii=False)

                        get_cw_data.fetch_from_monthly()


                        endtime = LOGcwl_player_cache[0]["war_info"]["endTime"] 

                        try:
                            with open(STAMPS["cwl"], "r") as f:
                                cwl_timestamp = f.read().strip()

                        except FileNotFoundError:
                            cwl_timestamp = ""

                        if endtime != cwl_timestamp or not cwl_timestamp:
                            save_cwl(LOGcwl_player_cache, endtime)

                        if season[1] == "ended" and seasonstamp == "inWar":

                            if endtime == cwl_timestamp:
                                save_cwl(LOGcwl_player_cache, endtime)

                            else:

                                try:
                                    with open(STAMPS["war_counter"], "r") as f:
                                        war_counter = int(f.read().strip())

                                    with open(STAMPS["war_counter"], "w") as f:
                                        f.write(str(war_counter + 7))

                                except (FileNotFoundError, ValueError):
                                    war_counter = 7

                                top10_monthly_data = get_cw_data.data_from_monthly()
                                top10_monthly = get_cw_data.fetch_from_top10(top10_monthly_data)

                                cwl_rompis = get_cw_data.cwl_rompis()
                                get_cw_data.fetch_from_mvp(top10_monthly[1])
                                get_cw_data.fetch_from_rompis(top10_monthly[2], cwl_rompis)

                                get_cw_data.reset_cwl()
                                get_cw_data.save_mothly()


                                print("alt lagret")

                                future = datetime.now(timezone.utc) + timedelta(days=2)
                                future_str = future.strftime("%Y%m%dT%H%M%S.000Z")
                                theme_ = {
                                    "theme": "top10",
                                    "warInfo": {
                                        "endTime": future_str
                                    }
                                }


                                with open(CACHE["theme"], "w", encoding="utf-8") as f:
                                    json.dump(theme_, f, indent=2, ensure_ascii=False)

                                with open(STAMPS["cwl_season"], "w") as f:
                                    f.write(f"ended, {season[0]}")
                
                                with open(STAMPS["war_counter"], "w") as f:
                                    f.write(str(0))

                                print("sesongen over, alt lagret riktig...")

                    else:
                        with open(STAMPS["war_tags_cwl"], "w") as f:
                            json.dump([], f)

            else:
                
                print("ingen krig!")
                with open(CACHE["theme"], "w", encoding="utf-8") as f:
                    json.dump(theme, f, indent=2, ensure_ascii=False)

                get_cw_data.get_clan_mebers()
                count = 60

        except Exception as e:
            print(f"Loop error: {e}")
            count = 30

        time.sleep(count)

def save_cwl(data, endtime):
    cwl_player_cache = data[0]

    print("gjennom endtime blokken")
    get_cw_data.save_cwl(cwl_player_cache)
    get_cw_data.fetch_from_LIVEmonthly(cwl_player_cache)

    top10_monthly_data = get_cw_data.data_from_monthly()
    top10_monthly = get_cw_data.fetch_from_top10(top10_monthly_data)

    backup.backup_database(DB["cw"], endtime=endtime)
    backup.rotate_backups()

    with open(STAMPS["cwl"], "w") as f:
        f.write(endtime)

    print("FERDIG")


if __name__ == "__main__":
    cw_loop()
