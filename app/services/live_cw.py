    
class LiveCW():
    def __init__(self, data, akk_points):
        self.akk_points = akk_points
        self.data = data
        self.war_count = 1
        self.clan_stars = data["clan"]["stars"]
        self.opp_stars = data["opponent"]["stars"]
        self.clan_badge = self.data["clan"]["badgeUrls"]["medium"]
        self.opp_clan = self.data["opponent"]["name"]
        self.opp_badge = self.data["opponent"]["badgeUrls"]["medium"]
        self.member = self.data["clan"]["members"]
        self.opponent = self.data["opponent"]["members"]
        self.wars_attended = 1

        self.endTime = self.data["endTime"]
        self.state = self.data["state"]
        self.teamsize = self.data["teamSize"]
        self.prepTime = self.data["preparationStartTime"]
        self.startTime = self.data["startTime"]

    def build_clan_attack_summary(self):
        clan_members = self.data["clan"]["members"]
        opponent_members = self.data["opponent"]["members"]

        opp_info = {}
        for member in opponent_members:
             opp_info[member["tag"]] = {
                  "townhallLevel":  member["townhallLevel"],
                  "mapPosition": member["mapPosition"]
             }



        result = {}
        result["war_info"] = {"endTime": self.endTime,
                            "warType": "cw",
                            "preparationStartTime": self.prepTime,
                            "startTime": self.startTime,
                            "state": self.state,
                            "teamSize": self.teamsize,
                            "oppName": self.opp_clan,
                            "warAttended": self.wars_attended,
                            "oppBadge": self.opp_badge,
                            "clanBadge": self.clan_badge,
                            "clanPoints": round(self.akk_points, 1),
                            "clanStars": self.clan_stars,
                            "oppStars": self.opp_stars,
                            "maxPoints": 100,
                            "scale": 1,
                            "war_count": self.war_count,
                            "oppInfo": opp_info,
                            "maxPoints_info": "maks er 100 poeng - bonus"
                            }
             
        
        for member in clan_members:
            tag = member["tag"]
            name = member["name"]
            townhall = member["townhallLevel"]

            player_info = {
                "name": name,
                "townhallLevel": townhall,
            }

            if "attacks" in member:
                attacks_used = len(member["attacks"])
                player_info["attacksUsed"] = attacks_used
                player_info["totalStars"] = sum(a["stars"] for a in member["attacks"])
                player_info["totalDestruction"] = sum(a["destructionPercentage"] for a in member["attacks"])

                attack_list = []
                for attack in member["attacks"]:
                    defender_tag = attack["defenderTag"]
                    defender = next((m for m in opponent_members if m["tag"] == defender_tag), {})
                    attack_list.append({
                        "defenderTag": defender_tag,
                        "defenderName": defender.get("name", "ukjent"),
                        "defenderTownhall": defender.get("townhallLevel", "ukjent"),
                        "stars": attack["stars"],
                        "destructionPercentage": attack["destructionPercentage"],
                        "duration": attack["duration"]
                    })
                player_info["attacks"] = attack_list
                
            else:
                player_info["attacksUsed"] = 0
                player_info["totalStars"] = 0
                player_info["totalDestruction"] = 0
                player_info["attacks"] = 0

            result[tag] = player_info

        return result
    
    def add_points(self):
        self.new_dic = self.build_clan_attack_summary()
        for tag, info in self.new_dic.items():
            if tag == "war_info":
                    continue 
            
            self.stars = info["totalStars"]
            self.destruction = info["totalDestruction"]
            self.townhall = info["townhallLevel"]

            attacks = info.get("attacks")
            if not attacks:
                self.points = 0
                unfiltered_points = 0
                self.potential_points = 0
                self.potential_bonus = 0
                self.star_points = 0

            else:
                total_th = sum(a["defenderTownhall"] for a in attacks)
                self.avg_def_th = (int(total_th) / len(attacks))

                self.normal_stars = self.stars / (info["attacksUsed"] * 3)
                self.star_points = self.stars / info["attacksUsed"] 

                self.penalty = False
                for _ in range(info["attacksUsed"]):
                    if (attacks[_]["defenderTownhall"] < self.townhall) and attacks[_]["stars"] < 3:
                            self.penalty = True
                            break
                
                if self.penalty:
                    self.th_points = min((self.avg_def_th / self.townhall) ** 3, 1)

                else:
                    self.th_points = min((self.avg_def_th / self.townhall) ** 2, 1)

                if self.townhall == 18:
                        unfiltered_points = self.normal_stars * self.th_points
                        self.points = unfiltered_points * 0.95
                        th_pen = 0

                elif self.townhall == 17:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = unfiltered_points * 0.93
                    th_pen = 0.04

                elif self.townhall == 16:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = unfiltered_points * 0.90
                    th_pen = 0.07
                
            
                elif self.townhall == 15:
                        unfiltered_points = self.normal_stars * self.th_points
                        self.points = unfiltered_points * 0.865
                        th_pen = 0.1
                    
                elif self.townhall == 14:
                        unfiltered_points = self.normal_stars * self.th_points
                        self.points = unfiltered_points * 0.85
                        th_pen = 0.125
                        
                else:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = unfiltered_points * 0.8
                    th_pen = 0.14

                self.points =max(self.points - th_pen, 0.001)
                self.potential_points = max(self.normal_stars * self.th_points - th_pen, 0.001)
                self.potential_bonus = self.potential_points - self.points

                if info["attacksUsed"] == 1:
                    self.potential_points *= 0.67
                    self.potential_bonus *= 0.67
                    self.points *= 0.67

            unfiltered_points *= 100 
            self.potential_points *= 100
            self.potential_bonus *= 100
            self.points *= 100

            self.new_dic[tag]["score"] = {"points": f"{self.points:.1f}",
                                            "maxPoints": f"{self.potential_points:.1f}",
                                            "unfilteredPoints": round(unfiltered_points, 3),
                                            "potentialBonus": f"{self.potential_bonus:.1f}",
                                            "starPoints": f"{self.star_points:.1f}"}
        return self.new_dic


             


         