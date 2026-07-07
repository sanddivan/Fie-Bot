import json
import os
from fie_trails.character import Character
from fie_trails import orbment_manager, item_manager

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "users")
DEFAULT_FIRST_BOSS = "gargoyle"
SLOTS = 6
DEFAULT_WEAPON = "kazekiri"
DEFAULT_ARMOR = "leather_guard"


def _user_path(user_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{user_id}.json")


def _default_save() -> dict:
    return {
        "character": {
            "name": "Rean Schwarzer",
            "current_xp": 0,
            "mira": 0,
        },
        "unlocked_bosses": [DEFAULT_FIRST_BOSS],
        "owned_orbments": [],
        "equipped_orbments": [None] * SLOTS,
        "inventory": [],
        "eq_inventory": [
            {"id": DEFAULT_WEAPON, "slot": "weapon"},
            {"id": DEFAULT_ARMOR, "slot": "armor"},
        ],
        "equipped": {
            "weapon": DEFAULT_WEAPON,
            "armor": DEFAULT_ARMOR,
            "accessory": None,
        },
    }


def load(user_id: int) -> tuple[Character, list[str], list[dict], list[dict]]:
    """
    Load a user's save. Creates a default save if none exists.
    Returns (character, unlocked_boss_ids, inventory, eq_inventory).
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
        mira=char_data.get("mira", 0),
    )

    # Resolve orbments
    character.available_orbments = orbment_manager.resolve_owned(
        save.get("owned_orbments", [])
    )
    character.equipped_orbments = orbment_manager.resolve_equipped(
        save.get("equipped_orbments", [None] * SLOTS)
    )

    # Restore equipped equipment then apply all bonuses
    character.equipped = save.get("equipped", {
        "weapon": DEFAULT_WEAPON,
        "armor": DEFAULT_ARMOR,
        "accessory": None,
    })
    character.refresh_equipped_arts()  # also calls apply_orbment_bonuses → apply_equipment_bonuses
    character.initialize_rean()

    inventory = item_manager.resolve_inventory(save.get("inventory", []))

    from fie_trails.equipment_manager import resolve_equipment_inventory
    eq_inventory = resolve_equipment_inventory(save.get("eq_inventory", []))

    return character, save["unlocked_bosses"], inventory, eq_inventory


def save(
    user_id: int,
    character: Character,
    unlocked_bosses: list[str],
    inventory: list[dict],
    eq_inventory: list[dict],
) -> None:
    """Persist all user state."""
    path = _user_path(user_id)

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
            "mira": character.mira,
        },
        "unlocked_bosses": unlocked_bosses,
        "owned_orbments": owned_ids,
        "equipped_orbments": equipped_ids,
        "inventory": inventory,
        "eq_inventory": eq_inventory,
        "equipped": character.equipped,
    }
    _write(path, data)


def add_orbment_drops(
    user_id: int,
    character: Character,
    unlocked_bosses: list[str],
    dropped_ids: list[str],
) -> list[str]:
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
    next_boss = beaten_boss.get("unlocks_next")
    if next_boss and next_boss not in unlocked_bosses:
        unlocked_bosses.append(next_boss)
    return unlocked_bosses


def _write(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)