import json
import os
from fie_trails.character import Character
from fie_trails import orbment_manager

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "users")
DEFAULT_FIRST_BOSS = "gargoyle"
SLOTS = 6


def _user_path(user_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{user_id}.json")


def _default_save() -> dict:
    return {
        "character": {
            "name": "Rean Schwarzer",
            "current_xp": 0,
        },
        "unlocked_bosses": [DEFAULT_FIRST_BOSS],
        "owned_orbments": [],
        "equipped_orbments": [None] * SLOTS,
    }


def load(user_id: int) -> tuple[Character, list[str]]:
    """
    Load a user's save. Creates a default save if none exists.
    Returns (character, unlocked_boss_ids).
    """
    path = _user_path(user_id)

    if not os.path.exists(path):
        save = _default_save()
        _write(path, save)
    else:
        with open(path, "r", encoding="utf-8") as f:
            save = json.load(f)

    char_data = save["character"]
    character = Character(
        name=char_data["name"],
        current_xp=char_data["current_xp"],
    )

    # Resolve orbment IDs into objects and apply to character
    character.available_orbments = orbment_manager.resolve_owned(
        save.get("owned_orbments", [])
    )
    character.equipped_orbments = orbment_manager.resolve_equipped(
        save.get("equipped_orbments", [None] * SLOTS)
    )
    character.refresh_equipped_arts()
    character.initialize_rean()

    return character, save["unlocked_bosses"]


def save(user_id: int, character: Character, unlocked_bosses: list[str]) -> None:
    """Persist XP, unlocked bosses, and orbment state for a user."""
    path = _user_path(user_id)

    # Serialize orbments back to IDs for storage
    all_defs = orbment_manager._load_all()
    name_to_id = {v["name"]: k for k, v in all_defs.items()}

    owned_ids = [
        name_to_id[o.name]
        for o in character.available_orbments
        if o.name in name_to_id
    ]
    equipped_ids = [
        name_to_id[o.name] if o and o.name in name_to_id else None
        for o in character.equipped_orbments
    ]

    data = {
        "character": {
            "name": character.name,
            "current_xp": character.current_xp,
        },
        "unlocked_bosses": unlocked_bosses,
        "owned_orbments": owned_ids,
        "equipped_orbments": equipped_ids,
    }
    _write(path, data)


def add_orbment_drops(
    user_id: int,
    character: Character,
    unlocked_bosses: list[str],
    dropped_ids: list[str],
) -> list[str]:
    """
    Add dropped orbment IDs to the character's available pool,
    skipping any already owned or equipped. Returns the list of
    actually new orbment names for the victory message.
    """
    all_defs = orbment_manager._load_all()
    name_to_id = {v["name"]: k for k, v in all_defs.items()}

    owned_ids = {name_to_id[o.name] for o in character.available_orbments if o.name in name_to_id}
    equipped_ids = {
        name_to_id[o.name]
        for o in character.equipped_orbments
        if o and o.name in name_to_id
    }
    already_have = owned_ids | equipped_ids

    new_orbments = []
    for oid in dropped_ids:
        if oid not in already_have and oid in all_defs:
            character.available_orbments.append(orbment_manager.build_orbment(all_defs[oid]))
            new_orbments.append(all_defs[oid]["name"])

    return new_orbments


def unlock_next_boss(unlocked_bosses: list[str], beaten_boss: dict) -> list[str]:
    """
    Given the boss dict from enemies.json that was just beaten,
    unlock the next boss if there is one and it isn't already unlocked.
    Returns the updated unlocked_bosses list.
    """
    next_boss = beaten_boss.get("unlocks_next")
    if next_boss and next_boss not in unlocked_bosses:
        unlocked_bosses.append(next_boss)
    return unlocked_bosses


def _write(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)