class EnemyCraft:
    def __init__(
        self,
        name: str,
        craft_type: str,        # "attack", "buff", "shield"
        cost: int,
        damage: int = 0,        # only used for attack crafts
        stat: str | None = None,        # only used for buff crafts
        multiplier: float = 1.0,        # only used for buff crafts
        turns: int = 0,                 # only used for buff crafts
    ):
        self.name = name
        self.craft_type = craft_type
        self.cost = cost
        self.damage = damage
        self.stat = stat
        self.multiplier = multiplier
        self.turns = turns

    def __str__(self):
        return self.name