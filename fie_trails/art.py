from enum import Enum
from fie_trails.element import Element


class ArtType(Enum):
    OFFENSIVE = "offensive"
    SUPPORT = "support"


class Art:
    def __init__(
        self,
        name: str,
        damage: int,
        cost: int,
        element: Element,
        art_type: ArtType = ArtType.OFFENSIVE,
        effect: str | None = None,
    ):
        self.name = name
        self.damage = damage
        self.cost = cost
        self.element = element
        self.art_type = art_type
        self.effect = effect  # e.g. "heal_hp:250"

    def __str__(self):
        return f"{self.name} - {self.cost} EP"