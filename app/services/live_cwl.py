
class LiveCWL():
    def __init__(self, data, scale, war_count, akk_points):
        self.data = data
        self.akk_points = akk_points
        self.home = data["side"]
        self.scale = scale
        self.war_count = war_count
        if self.home == "clan":
            self.clan_stars = self.data["clan"]["stars"]
            self.opp_stars = self.data["opponent"]["stars"]
            self.clan_badge = self.data["clan"]["badgeUrls"]["medium"]
            self.opp_clan = self.data["opponent"]["name"]
            self.opp_badge = self.data["opponent"]["badgeUrls"]["medium"]
            self.opponent = self.data["opponent"]["members"]
            self.member = self.data["clan"]["members"]
        else:
            self.clan_stars = self.data["opponent"]["stars"]
            self.opp_stars = self.data["clan"]["stars"]
            self.clan_badge = self.data["opponent"]["badgeUrls"]["medium"]
            self.opp_clan = self.data["clan"]["name"]
            self.opp_badge = self.data["clan"]["badgeUrls"]["medium"]
            self.opponent = self.data["clan"]["members"]
            self.member = self.data["opponent"]["members"]

        self.wars_attended = 1

        self.endTime = self.data["endTime"]
        self.state = self.data["state"]
        self.teamsize = self.data["teamSize"]
        self.prepTime = self.data["preparationStartTime"]
        self.startTime = self.data["startTime"]

    def build_clan_attack_summary(self):

        if self.home == "clan":
            clan_members = self.data["clan"]["members"]
            opponent_members = self.data["opponent"]["members"]
        else:
            clan_members = self.data["opponent"]["members"]
            opponent_members = self.data["clan"]["members"]

        result = {}
        result["war_info"] = {"endTime": self.endTime,
                            "warType": "cwl",
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
                            "maxPoints": round(100 * self.scale, 1),
                            "scale": self.scale,
                            "war_count": self.war_count,
                            "maxPoints_info": "Regnes slik at maks poeng fra forrige måndens clan wars er 3 ekstra stjerner i clan war league sammendraget"
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
                    self.destruction = attack["destructionPercentage"]
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
            super_attack = None

            attacks = info.get("attacks")
            if not attacks:
                self.points = 0
                unfiltered_points = 0

            else:
                total_th = sum(a["defenderTownhall"] for a in attacks)
                self.avg_def_th = (int(total_th) / len(attacks))
                self.normal_stars = self.stars / 3
                self.penalty = False
                for _ in range(info["attacksUsed"]):
                    if (attacks[_]["defenderTownhall"] < self.townhall) and attacks[_]["stars"] < 3:
                            self.penalty = True
                            break
                    
                    if attacks[_]["defenderTownhall"] > self.townhall and attacks[_]["stars"] >= 2:
                            super_attack = (attacks[_]["defenderTownhall"])
                            break
                
                if self.destruction >= 25 and self.destruction < 100:
                    norm_destruction = self.destruction / 1000
                    bonus = norm_destruction * 0.6

                else:
                    bonus = 0
                
                if self.penalty:
                    self.th_points = min((self.avg_def_th / self.townhall) ** 2, 1)

                else:
                    self.th_points = min((self.avg_def_th / self.townhall) ** 1.2, 1)

                if self.townhall == 18 or super_attack == 18:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = unfiltered_points + bonus

                elif self.townhall == 17 or super_attack == 17:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = (unfiltered_points + bonus) * 0.95

                elif self.townhall == 16 or super_attack == 16:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = (unfiltered_points + bonus) * 0.93
                
                elif self.townhall == 15 or super_attack == 15:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = (unfiltered_points + bonus) * 0.9
                    
                elif self.townhall == 14 or super_attack == 14:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = (unfiltered_points + bonus) * 0.89   
                        
                else:
                    unfiltered_points = self.normal_stars * self.th_points
                    self.points = (unfiltered_points + bonus) * 0.88

            self.points *= 100 * self.scale

            self.new_dic[tag]["score"] = {"points": round(self.points, 1),
                                          "unfilteredPoints": round(unfiltered_points * 100, 3)}

        return self.new_dic


             


         