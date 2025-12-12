from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.services.get_cw_data import fetch_from_monthly
from app.services import backup
from app.services import reset
import os, time
from pathlib import Path
import sqlite3
import json
import threading
from app.worker.updater import cw_loop
from app.services.get_cw_data import data_from_monthly
from app.paths import DB, CACHE, STAMPS

app = FastAPI()

@app.on_event("startup")
def start_worker():

    t = threading.Thread(target=cw_loop, daemon=True)
    t.start()


def fetch_from_player(tag):
    player = {}
    DB_PATH = DB["cw"]
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM player_cwlog WHERE tag = ?", (tag,))
    row = c.fetchone()
    conn.close()

    if row:
        p = row
        avrg_points = round(p[8] / p[9], 1)
        precent_attacks = round(p[7] / p[12], 2)
        player[tag] = {
                   "name": p[1],
                    "townhall": p[2],
                    "sum_stars": p[3],
                    "avrg_stars": p[5],
                    "avrg_attacks_used": p[6],
                    "sum_attacks_used": p[7],
                    "sum_points": round(p[8], 1),
                    "wars_attended": p[9],
                    "player_rating": p[10],
                    "possible_attacks": p[12],
                    "avrg_points": avrg_points,
                    "precent_attacks": precent_attacks * 100
                    }

        return player
    
    else:

        with open(CACHE["clan_members"], "r", encoding="utf-8") as f:
            data = json.load(f)
        
        player_ = data.get(tag, {})
        name = player_.get("name")
        townhall = player_.get("townhall")
        rating = player_.get("rating")

        player[tag] = {
                    "name": name,
                    "townhall": townhall,
                    "sum_stars": "0",
                    "avrg_stars": "0",
                    "avrg_attacks_used": "0",
                    "sum_attacks_used": "0",
                    "sum_points": "0",
                    "wars_attended": "0",
                    "player_rating": rating,
                    "possible_attacks": "0",
                    "avrg_points": "0",
                    "precent_attacks": "0"
                    }
        
        return player


@app.get("/clash/th-stats")
def get_stars():
    th_stats = {}
    return None
    

@app.get("/clash/player/{tag}") #husk at frontend må fjærne #
def get_player(tag: str):
    norm_tag = f"#{tag.upper()}"
    return fetch_from_player(norm_tag)

@app.get("/clash/clan-members")
def get_clan_members():
    try:
        with open(CACHE["clan_members"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")
    
@app.get("/clash/live-monthly")
def get_all_monthly():
    try:
        with open(CACHE["all_monthly"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")

@app.get("/clash/live-cw")
def get_LIVEcw():
    try:
        with open(CACHE["live_war"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")
    
@app.get("/clash/log-cwl")
def get_LOGcw():
    try:
        with open(CACHE["logcw"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")
    
def json_utf8(data):
    return JSONResponse(content=data, media_type="application/json; charset=utf-8")
    
@app.get("/clash/mvp")
def get_mvp():
    try:
        with open(CACHE["mvp"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return json_utf8(data)
    
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")

@app.get("/clash/rompis")
def get_rompis():
    try:
        with open(CACHE["rompis"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")
    
@app.get("/clash/top10-month")
def get_top10_month():
    try:
        with open(CACHE["top10_month"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")

@app.get("/clash/theme")
def theme():
    try:
        with open(CACHE["theme"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")

@app.get("/debug/where")
def where():
    return {
        "cwd": os.getcwd(),
        "list_cache": list(Path("data/cache_files").glob("*")),
    }

@app.get("/debug/mtimes")
def mtimes():
    out = {}
    p = Path("data/cache_files")
    for name in ["LIVE-war.json", "theme.json", "mvp.json", "clan_members.json"]:
        f = p / name
        if f.exists():
            out[name] = {
                "exists": True,
                "mtime_epoch": f.stat().st_mtime,
                "mtime_human": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(f.stat().st_mtime)),
                "size": f.stat().st_size,
            }
        else:
            out[name] = {"exists": False}
    return out

# app/api.py
import httpx

@app.get("/clash/wartag")
def wartag():
    try:
        with open(STAMPS["war_tags_cwl"], "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise HTTPException(404, "Filen finnes ikke")
    
    except json.JSONDecodeError:
        raise HTTPException(500, "Feilen var at JSON var ødelagt")

@app.get("/debug/egress-ip")
async def egress_ip():
    async with httpx.AsyncClient(timeout=5) as client:
        ip = (await client.get("https://api.ipify.org")).text
    return {"ip": ip}
