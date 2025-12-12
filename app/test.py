from app.paths import CACHE
import json

with open(CACHE["live_war"], "r") as f:
    data = json.load(f)

print(data)
