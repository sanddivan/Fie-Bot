from fie_trails.craft import Craft
from fie_trails.art import Art
from fie_trails.element import Element
from fie_trails.orbment import Orbment
from dataclasses import dataclass, field
from fie_trails.scraft import SCraft


@dataclass
class Character:
        name: str
        current_xp: int

        # Base stats
        base_max_hp: int = 500
        base_ep: int = 100
        base_cp: int = 0
        base_str: int = 20
        base_def: int = 15
        base_spd: int = 10
        base_ats: int = 12
        base_adf: int = 10

        # Growth per level
        growth_hp: int = 40
        growth_ep: int = 5
        growth_sp_stats: int = 2  # STR, DEF, ATS and ADF
        growth_spd: int = 1

        # Scaled stats
        # Computed on init
        level: int = field(init=False)
        max_hp: int = field(init=False)
        current_hp: int = field(init=False)
        ep: int = field(init=False)
        current_ep: int = field(init=False)
        cp: int = field(init=False)
        str: int = field(init=False)
        dfs: int = field(init=False)
        spd: int = field(init=False)
        ats: int = field(init=False)
        adf: int = field(init=False)

        crafts: list["Craft"] = field(init=False, default_factory=list)
        s_crafts: list["SCraft"] = field(init=False, default_factory=list)
        available_orbments: list["Orbment"] = field(init=False, default_factory=list)
        equipped_orbments: list["Orbment"] = field(init=False, default_factory=list)
        equipped_arts: list["Art"] = field(init=False, default_factory=list)

        # Note: This is merely an example for Rean
        def initialize_rean(self):
            if self.level >= 2:
                self.crafts.append(Craft("Motivate", 0, 10))
            if self.level >= 15:
                self.crafts.append(Craft("Arc Slash", self.str * 2, 30))
            if self.level >= 35:
                self.crafts.append(Craft("Gale", self.str * 3, 35))
            if self.level >= 55:
                self.crafts.append(Craft("Flame Impact", self.str * 4, 35))
            if self.level >= 5:
                self.s_crafts.append(SCraft("S-Craft Flame Slash", self.str * 10, 200))

            for orbment in self.equipped_orbments:
                if orbment.art_produced is not None:
                    self.equipped_arts.append(orbment.art_produced)

        def __post_init__(self):
            self.level = self.calculate_level()

            # Scaled stats
            self.refresh_stats()
            self.current_hp = self.max_hp
            self.current_ep = self.base_ep
            self.cp = self.base_cp

            # Initialize crafts/orbments/arts
            self.crafts = [Craft("Autumn Leaf Cutter", self.str * 2, 20)]
            fire_art = Art("Fire Bolt", self.str * 2, 20, Element.FIRE)

            self.available_orbments = [
                Orbment("Attack 1", 0, Element.FIRE, fire_art)
            ]
            self.equipped_orbments = [
                Orbment("Attack 2", 0, Element.FIRE, fire_art)
            ]

            # Pull arts from equipped orbments
            self.equipped_arts = []

        # Please please please don't do this. Use dataclasses instead. And also in general,
        # remember that Python never ever uses camelCase.

        def set_xp(self, xp: int):
            self.current_xp = xp
            old_level = self.level
            self.level = self.calculate_level()

            # If level changed, update stats
            if self.level != old_level:
                self.refresh_stats()

        def __str__(self):
            return str(self.crafts)

        def status(self):
            return (f"Name: {self.name}\n"
                    f"Level: {self.level}\n"
                    f"HP:  {self.max_hp}       EXP: {self.current_xp}\n"
                    f"STR: {self.str}      ATS: {self.ats}\n"
                    f"DEF: {self.dfs}      ADF: {self.adf}\n"
                    f"SPD: {self.spd}\n")

        def calculate_level(self):
            return int((self.current_xp ** 0.5) / 10) + 1

        def refresh_stats(self):
            self.max_hp = self.base_max_hp + self.growth_hp * self.level
            self.ep = self.base_ep + self.growth_ep * self.level
            self.str = self.base_str + self.growth_sp_stats * self.level
            self.dfs = self.base_def + self.growth_sp_stats * self.level
            self.spd = self.base_spd + self.growth_spd * self.level
            self.ats = self.base_ats + self.growth_sp_stats * self.level
            self.adf = self.base_adf + self.growth_sp_stats * self.level
            #self.current_hp = min(self.current_hp, self.max_hp)


        def reset(self):
            # Restore attributes from the initial state
            self.current_hp = self.max_hp