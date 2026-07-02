import json
import os
from fie_trails.character import Character

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "characters")
DEFAULT_FIRST_BOSS = "dino"


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
    character.initialize_rean()

    return character, save["unlocked_bosses"]


def save(user_id: int, character: Character, unlocked_bosses: list[str]) -> None:
    """Persist XP and unlocked bosses for a user."""
    path = _user_path(user_id)
    data = {
        "character": {
            "name": character.name,
            "current_xp": character.current_xp,
        },
        "unlocked_bosses": unlocked_bosses,
    }
    _write(path, data)


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