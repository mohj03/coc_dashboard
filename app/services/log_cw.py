
class CW_Log():
    def __init__(self, data):
        self.data = data
        self.opp_name = self.data["items"][0]["opponent"]["name"]
        self.opp_tag = self.data["items"][0]["opponent"]["tag"]
        self.badge_url = self.data["items"][0]["opponent"]["badgeUrls"]["medium"]

        self.result = self.data["items"][0]["result"]
        self.clan_score = self.data["items"][0]["clan"]["stars"]
        self.opp_score = self.data["items"][0]["opponent"]["stars"]

        self.end_time = self.data["items"][0]["endTime"]
    
    def opp_clan(self):
        return self.opp_name, self.opp_tag, self.badge_url
    
    def war_log(self):
        return self.result, self.clan_score, self.opp_score
    
    def result_(self):
        if self.result == "win":
            return "uguwewewewughoa"
        else:
            return self.opp_name
    
    def to_JSON(self):
        return {
            "opponent": 
                {"name": self.opp_name, 
                 "endTime": self.end_time,
                 "tag": self.opp_tag,
                 "badge_url":self.badge_url},
            "score": 
            {"winner": str(self.result_()),
             "uguwewewewughoa_stars": self.clan_score,
             "opp_stars": self.opp_score,
            }
            }
        