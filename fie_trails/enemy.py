class Enemy:
    def __init__(self, name: str, max_HP: int, current_HP: int, EP: int, CP: int,
                 STR: int, DEF: int, SPD: int, ATS: int,
                 ADF: int, level: int, xp: int, crafts=None):

        if crafts is None:
            crafts = []
        self.name = name
        self.max_HP = max_HP
        self.current_HP = current_HP
        self.EP = EP
        self.CP = CP
        self.STR = STR
        self.DEF = DEF
        self.SPD = SPD
        self.ATS = ATS
        self.ADF = ADF
        self.level = level
        self.xp = xp
        self.crafts = crafts
        self._initial_state = {
            k: v for k, v in self.__dict__.items() if k != "_initial_state"
        }

    def get_name(self) -> str:
        return self.name

    def get_max_hp(self) -> int:
        return self.max_HP

    def get_current_hp(self) -> int:
        return self.current_HP

    def set_max_hp(self, max_HP: int):
        self.max_HP = max_HP

    def set_current_hp(self, current_HP: int):
        self.current_HP = current_HP

    def get_ep(self) -> int:
        return self.EP

    def set_ep(self, EP: int):
        self.EP = EP

    def get_cp(self) -> int:
        return self.CP

    def set_cp(self, CP: int):
        self.CP = CP

    def get_str(self) -> int:
        return self.STR

    def set_str(self, STR: int):
        self.STR = STR

    def get_def(self) -> int:
        return self.DEF

    def set_def(self, DEF: int):
        self.DEF = DEF

    def get_ats(self) -> int:
        return self.ATS

    def set_ats(self, ATS: int):
        self.ATS = ATS

    def get_adf(self) -> int:
        return self.ADF

    def set_adf(self, ADF: int):
        self.ADF = ADF

    def get_xp(self) -> int:
        return self.xp

    def get_specific_craft(self, index: int):
        return self.crafts[index]

    def get_crafts(self):
        return self.crafts

    def __str__(self):
        return str(self.crafts)

    def reset(self):
        for k, v in self._initial_state.items():
            setattr(self, k, v)