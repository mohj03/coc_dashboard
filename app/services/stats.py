import sqlite3
class PlayerStat():
    def __init__(self, tag, th, attack_used, stars, star_points, points, max_points, mulig_bonus, wartype, c):
        self.tag = tag
        self.th = th
        self.attack_used_ = attack_used
        self.stars = stars
        self.star_points = star_points
        self.points = points
        self.max_points = max_points
        self.pos_bonus = mulig_bonus
        self.wartype = wartype

        if self.wartype == "cw":
            self.possible_attacks = 2
            self.ekstra = 0
        else:
            self.possible_attacks = 1
            self.ekstra = 1

        c.execute("SELECT sum_stars, sum_points, wars_attended, sum_attacks_used, avrg_stars, new, avrg_attacks_used FROM player_cwlog WHERE tag = ?", (self.tag,))
        result = c.fetchone()


        if result:
            self.avrg_stars_ = result[4]
            self.sum_stars = result[0] + self.stars
            self.sum_points = result[1] + self.points
            self.wars_attended = result[2] + 1
            self.attack_used = result[3] + self.attack_used_  + self.ekstra
            self.new = result[5]
            self.avrg_attacks = result[6]

        else:
            self.avrg_stars_ = 0
            self.sum_stars = self.stars
            self.sum_points = self.points
            self.wars_attended = 1
            self.attack_used = self.attack_used_
            self.new = 1


    def avrg(self):
        if self.new != 1:
            if self.attack_used == 0:
                self.avrg_stars = self.avrg_stars_

            else:
                self.avrg_stars = self.sum_stars / self.attack_used

            if self.wartype == "cwl":
                self.avrg_attacks_used = self.avrg_attacks
            else:
                self.avrg_attacks_used = self.attack_used  / (self.wars_attended * 2)

        else:
            if self.wartype == "cw":
                self.avrg_stars = self.star_points
            else:
                
                if self.attack_used == 0:
                    
                    self.avrg_stars = self.avrg_stars_

                else:
                    self.avrg_stars = self.sum_stars / self.attack_used

            self.avrg_attacks_used = self.attack_used / self.possible_attacks

        return round(self.avrg_stars, 1), round(self.avrg_attacks_used, 1)

    def _rating_(self):
        if self.th == 18:
            self.th_base = 88
        elif self.th == 17:
            self.th_base = 84
        elif self.th == 16:
            self.th_base = 82
        elif self.th == 15:
            self.th_base = 79
        elif self.th == 14:
            self.th_base = 74
        else:
            self.th_base = (self.th / 18) * 91

        if self.sum_points > 5000:
            self.points_base = 3
        elif self.sum_points > 3000:
            self.points_base = 2
        elif self.sum_points > 1000:
            self.points_base = 1
        else:
            self.points_base = 0

        if self.wars_attended > 500:
            self.war_base = 3
        elif self.wars_attended > 100:
            self.war_base = 2
        elif self.wars_attended > 10:
            self.war_base = 1
        elif self.wars_attended > 3:
            self.war_base = -1
        else:
            self.war_base = -3

        if self.avrg_stars > 2.6 and self.wars_attended > 100:
            self.star_base = 3
        elif self.avrg_stars > 2.5 and self.wars_attended > 10:
            self.star_base = 2
        elif self.avrg_stars > 2.7 and self.wars_attended > 5:
            self.star_base = 1
        elif self.avrg_stars <= 2.4 and self.avrg_stars >= 2 and self.wars_attended > 5:
            self.star_base = -3
        else:
            self.star_base = -5

        self.rating = int(self.th_base + self.points_base + self.war_base + self.star_base)

        return self.rating
    

    def tuple(self):
        self.avrg()
        self._rating_()
        self.new = 5

        return self.avrg_stars, self.avrg_attacks_used, self.rating, self.sum_points, self.new