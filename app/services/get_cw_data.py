import requests
from app.services.log_cw import CW_Log
from app.services.live_cw import LiveCW
from app.services.live_cwl import LiveCWL
from app.services import database
from app.services import helpers
import json
import os
from dotenv import load_dotenv
from app.services import cwl_database
from datetime import datetime, date
import google.generativeai as genai
import calendar
import random
from pprint import pprint

load_dotenv()
tok = os.getenv("CLASH_TOKEN") or os.getenv("COC_TOKEN") or os.getenv("CLASH_API_KEY") or ""
print("DEBUG CLASH TOKEN LEN:", len(tok))

GEMINI_API_KEY = os.getenv("GEMENI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-flash")

api_key = os.getenv("CLASH_API_KEY")
clan_tag = "#2PYRCQJJG"

cw_url = f"https://api.clashofclans.com/v1/clans/%232PYRCQJJG/warlog?limit=1"
cw_url_player = f"https://api.clashofclans.com/v1/clans/%232PYRCQJJG/currentwar"
cwl_url = f"https://api.clashofclans.com/v1/clans/%232PYRCQJJG/currentwar/leaguegroup"
clan_members_url = "https://api.clashofclans.com/v1/clans/%232PYRCQJJG/members"

def fetch_from_LIVEcw():

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    response_cw_player = requests.get(cw_url_player, headers=headers)
    theme = {}

    if response_cw_player.status_code == 200:
        current_data = response_cw_player.json()
        if current_data["state"] == "notInWar":
            return {}, {}, {}
        
        #with open("dummy_json/siste_krig.json", "r") as f: #fake
            _current_data = json.load(f)

        try:
            with open("data/cache_files/LIVE-war.json", "r") as f:
                data = json.load(f)
        
        except FileNotFoundError:
            data = {}
        akk_points = 0
        if  data:
            for key, val in data.items():
                if key == "war_info":
                    continue
                points = float(val["score"]["points"])
                akk_points += points

        ongoing = LiveCW(current_data, akk_points)
        live_cw_data_ = ongoing.add_points()


        theme = {
            "theme": "clanwar",
            "warInfo": live_cw_data_["war_info"]
        }

        with open("data/cache_files/LIVE-war.json", "w", encoding="utf-8") as f:
            json.dump(live_cw_data_, f, indent=2, ensure_ascii=False)
    

        print("LIVE-war.json oppdatert vellykket")
        return live_cw_data_, theme, current_data

    else:
        print("kunne ikke hente data")
        print(f"Live war: {response_cw_player.status_code}")
        return False

def fetch_from_LOGcw():

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    response_cw = requests.get(cw_url, headers=headers)

    if response_cw.status_code == 200:
        warlog_data = response_cw.json()
        CWlog = CW_Log(warlog_data)
        log_cw_data = CWlog.to_JSON()

        with open("data/cache_files/LOGcw.json", "w", encoding="utf-8") as f:
            json.dump(log_cw_data, f, indent=2, ensure_ascii=False)

        print("LOGcw.json oppdatert vellykket")
        return log_cw_data
        
    else:
        print("Klarte ikke hente data.")
        print(f"Warlog: {response_cw.status_code}")
        return False

def get_clan_mebers():
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    response_members = requests.get(clan_members_url, headers=headers)

    if response_members.status_code == 200:
        warlog_data = response_members.json()
        clan_list = database.clan_list(warlog_data)

        with open("data/cache_files/clan_members.json", "w",  encoding="utf-8") as f:
            json.dump(clan_list, f, indent=2, ensure_ascii=False)
            
        return True
    
    print("kunne ikke hente klanmedlemmer")
    return False


def save_LOGcw(data):
    database.save_warLog(data)

def cwl_check():
    cwl_url = f"https://api.clashofclans.com/v1/clans/%232PYRCQJJG/currentwar/leaguegroup"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    response_cwl = requests.get(cwl_url, headers=headers)

    if response_cwl.status_code != 200:
        print(f"Feil ved henting av leaguegroup: {response_cwl.status_code}")
        print("Responsinnhold:", response_cwl.text)
        return False
    
    try:
        current_data = response_cwl.json()
        state = current_data.get("state")
        season = current_data.get("season")

        if state in ["inWar", "preparation", "ended"]:
            return season, state
        
        else:
            return False

    except Exception as e:
        print(f"Feil ved JSON-parsing: {e}")
        return False


def get_wartag(tags):
    cwl_url = f"https://api.clashofclans.com/v1/clans/%232PYRCQJJG/currentwar/leaguegroup"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    response_cwl = requests.get(cwl_url, headers=headers)
    
    if response_cwl.status_code != 200:
        print(f"Feil ved henting av leaguegroup: {response_cwl.status_code}")
        print("Responsinnhold:", response_cwl.text)
        return []  # eller raise Exception("API-feil")

    try:
        current_data = response_cwl.json()
        
    except Exception as e:
        print(f"Feil ved JSON-parsing: {e}")
        return []
    

    if "rounds" not in current_data or not current_data["rounds"]:
        print("Ingen aktive CWL-runder funnet.")
        return False

    active_tag = (None, 0)
    if tags:
        for _ in range(len(tags)):
            if tags[_][1] == "inWar":
                active_tag = (tags[_][0], _)
                break
    
    start_index = active_tag[1]
    war_tags = []

    for _ in range(start_index, 7):
        tag1 = current_data["rounds"][_]["warTags"][0]
        
        if tag1 == "#0":
            break

        for i in range(len(current_data["rounds"][_]["warTags"])):
            correct_tag1 = current_data["rounds"][_]["warTags"][i]
            correct_tag = correct_tag1.replace("#", "")

            if active_tag[0] and active_tag[0] != correct_tag:
                continue

            cwl_round_url1 = f"https://api.clashofclans.com/v1/clanwarleagues/wars/%23{correct_tag}"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            }


            response_cwl1 = requests.get(cwl_round_url1, headers=headers)

            if response_cwl1.status_code != 200:
                print(f"Feil med {tag1}: {response_cwl1.status_code}")
                continue

            round_data = response_cwl1.json()
            state = round_data["state"]

            if round_data["clan"]["tag"] == "#2PYRCQJJG":
                val = (correct_tag, "clan", state)
                war_tags.append(val)
                break
            
            elif round_data["opponent"]["tag"] == "#2PYRCQJJG":
                val = (correct_tag, "opponent", state)
                war_tags.append(val)
                break
        
    with open("data/stamps/war_tags_cwl.json", "w") as f:
        json.dump(war_tags, f, indent=2)

    return war_tags

def get_cwl():
    war_data = None
    try:
        with open("data/stamps/war_tags_cwl.json", "r") as f:
            wt = json.load(f)

    except FileNotFoundError:
            wt = []

    if wt:
        old_tags = []
        for _ in range(len(wt)):
            tag = wt[_][0]
            state = wt[_][2]
            old_tags.append((tag, state))
    
    else:
        old_tags = []

    warTag = get_wartag(old_tags)

    theme = {}
    if not warTag:
        print("CWL har ikke startet")
        return {}, {}, False
    done = False
    target_idx = None
    update = False

    for i, (_, _, s) in enumerate(warTag):
        if s == "inWar":
            target_idx = i
            break

    if target_idx is None and len(warTag) >= 2:
        if warTag[-1][2] == "preparation" and warTag[-2][2] == "warEnded":
            target_idx = -2
            update = True
    
    if target_idx is None and len(warTag) == 7 and warTag[6][2] == "warEnded":
        target_idx = 6
        update = True
        done = True

    if target_idx is None and warTag[0][2] == "preparation":
        target_idx = 0

    if target_idx is None:
        print("Ingen aktiv/prep/nylig avsluttet CWL-kamp – henter ikke")
        return {}, {}, False, False

    tag_no_hash, side, _status = warTag[target_idx]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
        }
    
    cwl_round_url = f"https://api.clashofclans.com/v1/clanwarleagues/wars/%23{tag_no_hash}"
    response = requests.get(cwl_round_url, headers=headers)

    if response.status_code == 200:

        war_data = response.json()
        war_data["side"] = side
        try:
            with open("data/stamps/war_counter.txt", "r") as f:
                war_count = int(f.read().strip())
                scale_points = round((war_count * 95) / 100, 1)

        except (FileNotFoundError, ValueError):
            scale_points = 1

        try:
            with open("data/cache_files/LIVE-war.json", "r") as f:
                data = json.load(f)
        
        except FileNotFoundError:
            data = {}
        akk_points = 0
        if  data:
            for key, val in data.items():
                if key == "war_info":
                    continue
                points = val["score"]["points"]
                akk_points += points
        
        raff = LiveCWL(war_data, scale_points, war_count, akk_points)

        cwl_data = raff.add_points()

        with open("data/cache_files/LIVE-war.json", "w", encoding="utf-8") as f:
            json.dump(cwl_data, f, indent=2, ensure_ascii=False)

        theme = {
            "theme": "clanwarleague",
            "warInfo": cwl_data["war_info"]
        }
        print("LIVEcwl oppdatert vellykket!")
        return cwl_data, theme, update, done
    
    else:
        print("Klarte ikke hente data.")
        print(f"Warlog: {response.status_code}")

        return {}, {}, False, False


def reset_cwl():
    cwl_database.reset_cwl()

def save_cwl(data):
    cwl_database.save_cwlInfo(data)

def fetch_from_LIVEmonthly(data):
    try:
        with open("data/stamps/war_counter.txt", "r") as f:
                    war_count = int(f.read().strip())
                    scale_points = round((war_count * 95) / 100, 1)

    except (FileNotFoundError, ValueError):
                war_count = 1
                scale_points = 1

    return database.save_warInfo(data, scale_points)

def data_from_monthly():
    return database.monthly_cache()

def fetch_from_monthly():
    data = database.monthly_cache()
    with open("data/cache_files/all_monthly.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_mothly():
    database.monthly_score()

def monthly_rank():
    return database.monthly_cache()

def cwl_rompis():
    return cwl_database.cwl_rompis()

def worste_player_tag(data):
    loser_player = []

    try:
        with open("data/stamps/war_counter.txt", "r") as f:
            all_wars = int(f.read().strip())

    except ValueError:
        all_wars = 1

    for i, (tag, player) in enumerate(data.items()):
        wars = player.get("monthly_possible_wars")

        if wars == 0 or all_wars == 0:
            continue

        elif tag == "YLY98QCU":
            continue

        elif (wars / all_wars) >= 0.35:
            avrg_points = player.get("final_monthly_points", 0) / wars  
            stars = player.get("monthly_points", 0)
            val = tag, avrg_points
            loser_player.append(val)

    if loser_player:
        worst_player = min(loser_player, key=lambda x: x[1])
        tag = worst_player[0]
        player = data[tag]

    else:
        tag = None
        player = None

    return tag, player

def fetch_from_top10(data):
    top10 = {}
    mvp = {}
    worste_player = worste_player_tag(data)
    loser = worste_player[1]

    for i, (tag, player) in enumerate(data.items()):
        if i <= 9:
            player_info = {}
            if i == 0:
                player_info["comment"] = "MVP!"
                mvp[tag] = player

            elif tag == worste_player[0]:
                player_info["comment"] = "rompis!"

            else:
                player_info["comment"] = None
            
            if tag == "#L0P8RQJ8":
                if i == 0:
                    player_info["comment"] = "mvp, OLA sin 2. bruker"
                else:
                    player_info["comment"] = "OLA sin 2. bruker"

            elif tag == "#G8R9L08Y":
                if i == 0:
                    player_info["comment"] = "mvp, BP sin 2. bruker"
                else:
                    player_info["comment"] = "BP sin 2. bruker"

            elif tag == "#YJOQUJP2V":
                if i == 0:
                    player_info["comment"] = "mvp, TOGGA sin 2. bruker"
                else:
                    player_info["comment"] = "TOGGA sin 2. bruker"
                

            player_info["name"] = player.get("name")
            player_info["tag"] = player.get("tag")
            player_info["points"] = player.get("final_monthly_points")
            player_info["stars"] = player.get("monthly_stars")
            player_info["rating"] = player.get("rating")
            player_info["rank"] = player.get("rank")

            top10[tag] = player_info        

        with open("data/cache_files/top10_month.json", "w", encoding="utf-8") as f:
            json.dump(top10, f, indent=2, ensure_ascii=False)

    print("top10 rangert")

    return top10, mvp, loser

def fetch_from_mvp(mvp):

    mvp_ = {}
    now = datetime.now()
    month = 12 if now.month == 1 else now.month - 1
    award_type = "mvp"

    month_name = calendar.month_name[month]
    if not mvp:
        mvp_["name"] = None
        mvp_["headline"] = f"MVP for {month_name}"
        mvp_["comment"] = None
        mvp_["info"] = "Unknown error"

    else:
        tag_ = list(mvp.keys())[0]           
        player_data = mvp[tag_] 

        navn = player_data.get("name")
        poeng = player_data.get("final_monthly_points")
        max_poeng = player_data.get("monthly_max_points")
        prosent = player_data.get("precent")
        rangering = player_data.get("rating")
        stjerner = player_data.get("monthly_stars")

        melding = (
            f"Navnet på spilleren er {navn}. "
            f"oppsumering for {month}"
            f"Han fikk {poeng} poeng av {max_poeng} mulige. "
            f"Han gjorde {prosent} av alle mulige angrep. "
            f"Han er rangert {rangering}, og samlet {stjerner} stjerner."
        )

        chat ={
            "role": "system",
            "parts": ["Du er en analytiker og kommentator for Clash of Clans.", "Du lager "
            "underholdende og ærlige tekster som oppsummerer spillernes innsats i måneden.",
            "du skildrer grussome og ekle situasjoner fra krigen",
            "skriv det som en krigs tale (churchill preg), hvor slitene skadde traumatiserte soldater endelig kommer hjem",
            "han skal fremstå som en krigshelt"
            "maks 150-200 ord!",
            "avslutt med et veldig tilfeldig og grisete ordtak",
            "hva verdier betyr",
            "- navn: navn på spilleren.",
            "- poeng: samlet poengsum gjennom måneden.",
            "- prosent: prosent av angrep utført.",
            "- mulig poeng: prosent av angrep utført av poeng",
            "- rangering: rating fra 0 - 100., hvor 100 er helt ekstremt bra",
            "- stjerner: antall stjerner spilleren fikk i CW og CWL.",
            "Spilleren er denne månedens beste spiller!"
            ],
            "prompt": f"{melding}"
                }
            

        response = model.generate_content(
            contents=f"{chat}"
    )
        
        mvp_["name"] = navn
        mvp_["headline"] = f"MVP for {month_name} er {navn}"
        mvp_["comment"] = response.text
        mvp_["info"] = "(generert av gemini-2.5-flash API)"

    with open("data/cache_files/mvp.json", "w", encoding="utf-8") as f:
        json.dump(mvp_, f, indent=2, ensure_ascii=False)

    type_month = helpers.month(month)
    print(f"DEBUG: Trying to update database with tag: {tag_}")
    database.update_mvp_and_rompis(tag_, award_type, type_month, response.text)
    

def fetch_from_rompis(loser, cwl_rompis):
    if cwl_rompis:
        None
    uttrykk = ["skitheks, ludder, blodhore", "hei hei hei, det er ikke farlig", "det er veldig veldig veldig veldig viktig at vi får i oss nokka å drikke",
               "jævla rasshøl", "pikkoter", "soper", "flyr av gåre i en UFO sammen med Elvis, og Yetien",
               "Loch-Ness monsteret", "Hva for noe hvisking og sånn dere tisking?", "geniet Rock Fjellstad", "Homoen Tordenskjøld",
               "samen Jompa Tormann", "fastlegen Kjell Driver", "Pedoen Gregor Hykklerud", "fotografen Pablo", "Ligg i ro! Ligg i ro!"]


    tilfeldig_element = random.choice(uttrykk)

    loser_ = {}
    now = datetime.now()
    month = 12 if now.month == 1 else now.month - 1
    award_type = "rompis"
    type_month = helpers.month(month)

    month_name = calendar.month_name[month]
    if loser == None:
        loser_["name"] = None
        loser_["headline"] = f"Rompis for {month_name}"
        loser_["comment"] = None
        loser_["info"] = "Unknown error"
    
    else:        
        navn = loser.get("name")
        poeng = loser.get("final_monthly_points")
        max_poeng = loser.get("monthly_max_points")
        prosent = loser.get("precent")
        rangering = loser.get("rating")
        stjerner = loser.get("monthly_stars")
        tag = next(iter(loser))

        melding = (
            f"Navnet på spilleren er {navn}. "
            f"oppsumering for perioden: {month}"
            f"Han fikk {poeng} poeng av {max_poeng} mulige poeng. "
            f"Han gjorde {prosent} av alle mulige cw angrep. "
            f"Han har en rating på {rangering}, og samlet {stjerner} stjerner."
        )

        chat ={
            "role": "system",
            "parts": ["ditt navn er Burt Erik og er lensmann"
            "Du har krigskunnskap som en analytiker og kommentator for Clash of Clans.",
            "du presenterer månedens værste spiller"
            "Du oppfører def som en ondskapsfull, frekk og slem clash of clans major"
            "denne spilleren kommer hjem fra krig som en feit landssviker"
            "skjell han ordentlig ut"
            "alltid presenter deg selv først, altså Burt Erik"
            f"flett inn dette ordet eller utrykket på en kreativ måte!: {tilfeldig_element}"
            "maks 150 ord!",
            "hva verdier betyr",
            "- navn: navn på spilleren.",
            "- poeng: samlet poengsum gjennom måneden.",
            "- prosent: prosent av angrep utført.",
            "- mulig poeng: prosent av angrep utført av poeng",
            "- rangering: rating fra 0 - 100., hvor 100 er helt ekstremt bra, 70-80 er ok",
            "- stjerner: antall stjerner spilleren fikk tilsammen i CW og CWL.",
            f"Spilleren er  {month_name} - månedens lateste og værste spiller!"
            ],
            "prompt": f"{melding}"
                }
            

        response = model.generate_content(
            contents=f"{chat}"
    )
        
        loser_["name"] = navn
        loser_["headline"] = f"Rompis for {month_name} er {navn}"
        loser_["comment"] = response.text
        loser_["info"] = "(generert av gemini-2.5-flash API)"

    with open("data/cache_files/rompis.json", "w", encoding="utf-8") as f:
        json.dump(loser_, f, indent=2, ensure_ascii=False)

    database.update_mvp_and_rompis(tag, award_type, type_month, response.text)
    return cwl_rompis
    
if __name__ == "__main__":

    dummy_data = {
    "side": "clan",
    "state": "inWar",
    "teamSize": 15,
    "preparationStartTime": "20251003T095306.000Z",
    "startTime": "20251004T095304.000Z",
    "endTime": "20251005T095304.000Z",

    "clan": {
        "name": "Vår Klan",
        "stars": 3,
        "badgeUrls": {
            "medium": "https://api-assets.clashofclans.com/badges/200/GGcluS6WrbAPj2J6z8Z1W1rBSb3BUR0L3AOg0j6U_ec.png"
        },
        "members": [
            {"tag": "#YLY98QCU", "name": "Magnus O",   "townhallLevel": 17,
             "attacks": [{"defenderTag": "#DEF1",  "stars": 2, "destructionPercentage": 62, "duration": 0}]},

            {"tag": "#L0P8RQJ8", "name": "ola",        "townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF2",  "stars": 2, "destructionPercentage": 81, "duration": 0}]},

            {"tag": "#2YY2RGJ",  "name": "Åflæng",     "townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF3",  "stars": 0, "destructionPercentage": 0,  "duration": 0}]},

            {"tag": "#Y2QQV8VGQ","name": "Ola",        "townhallLevel": 17,
             "attacks": [{"defenderTag": "#DEF4",  "stars": 3, "destructionPercentage": 100, "duration": 0}]},

            {"tag": "#2YPLUVYQJ","name": "MiniMeno",   "townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF5",  "stars": 2, "destructionPercentage": 90, "duration": 0}]},

            {"tag": "#Y2VJC98U", "name": "AL19",       "townhallLevel": 17,
             "attacks": [{"defenderTag": "#DEF6",  "stars": 1, "destructionPercentage": 91, "duration": 0}]},

            {"tag": "#280PGV98", "name": "martinus",   "townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF7",  "stars": 3, "destructionPercentage": 100, "duration": 0}]},

            {"tag": "#C0CQJGPC", "name": "bobby shmurda","townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF8",  "stars": 2, "destructionPercentage": 77, "duration": 0}]},

            {"tag": "#29RQCRP80","name": "Moll”ester", "townhallLevel": 16,
             "attacks": [{"defenderTag": "#DEF9",  "stars": 2, "destructionPercentage": 70,   "duration": 0}]},

            {"tag": "#PP0JLQLGY","name": "HenrikAas",  "townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF10", "stars": 2, "destructionPercentage": 89, "duration": 0}]},

            {"tag": "#9PRUQLVVV","name": "molle390",   "townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF11", "stars": 2, "destructionPercentage": 66, "duration": 0}]},

            {"tag": "#20QCG9P92","name": "Togga0336",  "townhallLevel": 17,
             "attacks": [{"defenderTag": "#DEF12", "stars": 3, "destructionPercentage": 100, "duration": 0}]},

            {"tag": "#LRPJGYJPV","name": "Shring",     "townhallLevel": 15,
             "attacks": [{"defenderTag": "#DEF13", "stars": 1, "destructionPercentage": 45, "duration": 0}]},

            {"tag": "#YLCPGGLP9","name": "krizzybp",   "townhallLevel": 17,
             "attacks": [{"defenderTag": "#DEF14", "stars": 2, "destructionPercentage": 98, "duration": 0}]},

            {"tag": "#YCYLGQPP", "name": "Ilen200",    "townhallLevel": 17,
             "attacks": [{"defenderTag": "#DEF15", "stars": 2, "destructionPercentage": 96, "duration": 0}]}
        ]
    },

    "opponent": {
        "name": "England.com",
        "stars": 2,
        "badgeUrls": {
            "medium": "https://api-assets.clashofclans.com/badges/200/oaYTcWsfzShIKRCt21V1fGb0EoBrzrMNnTmCYHJ4cDc.png"
        },
        "members": [
            {"tag": "#DEF1",  "name": "def1",  "townhallLevel": 17},
            {"tag": "#DEF2",  "name": "def2",  "townhallLevel": 17},
            {"tag": "#DEF3",  "name": "def3",  "townhallLevel": 17},
            {"tag": "#DEF4",  "name": "def4",  "townhallLevel": 17},
            {"tag": "#DEF5",  "name": "def5",  "townhallLevel": 17},
            {"tag": "#DEF6",  "name": "def6",  "townhallLevel": 17},
            {"tag": "#DEF7",  "name": "def7",  "townhallLevel": 16},
            {"tag": "#DEF8",  "name": "def8",  "townhallLevel": 17},
            {"tag": "#DEF9",  "name": "def9",  "townhallLevel": 17},
            {"tag": "#DEF10", "name": "def10", "townhallLevel": 17},
            {"tag": "#DEF11", "name": "def11", "townhallLevel": 17},
            {"tag": "#DEF12", "name": "def12", "townhallLevel": 17},
            {"tag": "#DEF13", "name": "def13", "townhallLevel": 17},
            {"tag": "#DEF14", "name": "def14", "townhallLevel": 17},
            {"tag": "#DEF15", "name": "def15", "townhallLevel": 17}
        ]
    }
}
    hei = LiveCWL(dummy_data, 8.6, 1, 1)
    test = hei.add_points()
    pprint(test)

    

