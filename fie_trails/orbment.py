from enum import Enum
from fie_trails.art import Art


class Orbment:
    def __init__(
        self,
        name: str,
        status_change: int,
        stat: str | None,
        element: Enum | None,
        art_produced: Art | None = None,
    ):
        self.name = name
        self.status_change = status_change
        self.stat = stat          # character attribute to boost, e.g. "str" or "dfs"
        self.element = element
        self.art_produced = art_produced

    def __str__(self):
        bonus = f"+{self.status_change} {self.stat.upper()}" if self.stat else ""
        art = f" | {self.art_produced}" if self.art_produced else ""
        return f"{self.name} ({bonus}{art})"