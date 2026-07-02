import json
import os
import random
from fie_trails.orbment import Orbment
from fie_trails.art import Art
from fie_trails.element import Element

ORBMENTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "orbments.json")
SLOTS = 6


def _load_all() -> dict[str, dict]:
    """Returns all orbment definitions keyed by id."""
    with open(ORBMENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {o["id"]: o for o in data["orbments"]}


def build_orbment(orbment_data: dict) -> Orbment:
    """Construct an Orbment instance from a definition dict."""
    art = None
    if orbment_data.get("art"):
        a = orbment_data["art"]
        art = Art(a["name"], a["damage"], a["cost"], Element[a["element"]])
    return Orbment(
        orbment_data["name"],
        orbment_data["status_change"],
        Element[orbment_data["art"]["element"]] if orbment_data.get("art") else None,
        art,
    )


def resolve_owned(owned_ids: list[str]) -> list[Orbment]:
    """Turn a list of orbment IDs into Orbment objects."""
    all_orbments = _load_all()
    return [build_orbment(all_orbments[oid]) for oid in owned_ids if oid in all_orbments]


def resolve_equipped(equipped_ids: list[str | None]) -> list[Orbment | None]:
    """
    Turn the 6-slot equipped list (IDs or nulls) into Orbment objects or None.
    Always returns a list of exactly SLOTS entries.
    """
    all_orbments = _load_all()
    slots = (equipped_ids + [None] * SLOTS)[:SLOTS]
    return [
        build_orbment(all_orbments[oid]) if oid and oid in all_orbments else None
        for oid in slots
    ]


def roll_drops(boss_data: dict) -> list[str]:
    """
    Given a boss dict from enemies.json, roll each orbment drop
    and return a list of orbment IDs that were won.
    """
    won = []
    for drop in boss_data.get("orbment_drops", []):
        if random.random() < drop["chance"]:
            won.append(drop["id"])
    return won