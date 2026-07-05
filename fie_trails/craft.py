class Craft:
    def __init__(self, name: str, multiplier: float, cost: int):
        self.name = name
        self.multiplier = multiplier
        self.cost = cost

    def __str__(self):
        return f"{self.name} - {self.cost} CP"