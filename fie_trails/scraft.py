from fie_trails.craft import Craft

class SCraft(Craft):
    def __init__(self, name: str, multiplier: float, cost: int):
        super().__init__(name, multiplier, cost)