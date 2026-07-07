import json
import os
from discord import Client, Message
import asyncio

EQUIPMENT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "equipment.json")


def _load_all() -> dict:
    with open(EQUIPMENT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_available_equipment(unlocked_bosses: list[str]) -> dict:
    """Return weapons and armors available in the shop based on unlocked bosses."""
    all_eq = _load_all()
    return {
        "weapons": [
            w for w in all_eq["weapons"]
            if w["unlocked_by"] is None or w["unlocked_by"] in unlocked_bosses
        ],
        "armors": [
            a for a in all_eq["armors"]
            if a["unlocked_by"] is None or a["unlocked_by"] in unlocked_bosses
        ],
    }


def build_equipment_entry(item_id: str, slot: str) -> dict:
    """Build an inventory entry for a piece of equipment."""
    return {"id": item_id, "slot": slot}


def get_equipment_def(item_id: str) -> dict | None:
    """Return a single equipment definition by ID searching all slots."""
    all_eq = _load_all()
    for slot in ("weapons", "armors", "accessories"):
        for item in all_eq.get(slot, []):
            if item["id"] == item_id:
                return item
    return None


def resolve_equipment_inventory(inventory: list[dict]) -> list[dict]:
    """Remove any entries whose IDs no longer exist in equipment.json."""
    return [e for e in inventory if get_equipment_def(e["id"]) is not None]


def get_stat_bonuses(equipment_id: str) -> dict[str, int]:
    """Return a dict of stat bonuses for a piece of equipment."""
    eq_def = get_equipment_def(equipment_id)
    if eq_def is None:
        return {}
    return {
        k: v for k, v in eq_def.items()
        if k.endswith("_bonus")
    }


def format_equipment_entry(eq_def: dict) -> str:
    bonuses = []
    if eq_def.get("str_bonus"):
        bonuses.append(f"STR +{eq_def['str_bonus']}")
    if eq_def.get("def_bonus"):
        bonuses.append(f"DEF +{eq_def['def_bonus']}")
    if eq_def.get("adf_bonus"):
        bonuses.append(f"ADF +{eq_def['adf_bonus']}")
    bonus_str = ", ".join(bonuses)
    return f"{eq_def['name']} ({bonus_str}) — {eq_def['price']} mira"


async def wait_for_digit_reply(client, author, channel, timeout=120.0):
    def check(m):
        return (
            m.author == author
            and m.channel == channel
            and m.content.isdigit()
        )
    try:
        return await client.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        return None


async def show_equipment_shop(
    client_obj: Client,
    message_obj: Message,
    mira: int,
    eq_inventory: list[dict],
    unlocked_bosses: list[str],
) -> tuple[list[dict], int]:
    """
    Show the equipment shop. Returns (updated_eq_inventory, updated_mira).
    """
    src_channel = message_obj.channel
    available = get_available_equipment(unlocked_bosses)

    while True:
        lines = [f"**Equipment Shop** — You have {mira} mira\n"]

        lines.append("— Weapons —")
        for i, weapon in enumerate(available["weapons"]):
            owned = any(e["id"] == weapon["id"] for e in eq_inventory)
            suffix = " _(owned)_" if owned else ""
            lines.append(f"{i + 1} - {format_equipment_entry(weapon)}{suffix}")

        lines.append("\n— Armors —")
        offset = len(available["weapons"])
        for i, armor in enumerate(available["armors"]):
            owned = any(e["id"] == armor["id"] for e in eq_inventory)
            suffix = " _(owned)_" if owned else ""
            lines.append(f"{offset + i + 1} - {format_equipment_entry(armor)}{suffix}")

        lines.append("\n0 - Leave shop")
        await src_channel.send("\n".join(lines))

        choice = await wait_for_digit_reply(
            client_obj, message_obj.author, message_obj.channel
        )
        if choice is None:
            await src_channel.send("You took too long! Leaving the shop.")
            break

        chosen = int(choice.content)
        if chosen == 0:
            await src_channel.send("Come back anytime!")
            break

        total = len(available["weapons"]) + len(available["armors"])
        if chosen > total:
            await src_channel.send(
                f"That's not a valid choice! Pick a number between 1 and {total}."
            )
            continue

        if chosen <= len(available["weapons"]):
            eq_def = available["weapons"][chosen - 1]
            slot = "weapon"
        else:
            eq_def = available["armors"][chosen - offset - 1]
            slot = "armor"

        if any(e["id"] == eq_def["id"] for e in eq_inventory):
            await src_channel.send(f"You already own {eq_def['name']}!")
            continue

        if eq_def["price"] > mira:
            await src_channel.send(
                f"Not enough mira! {eq_def['name']} costs {eq_def['price']} "
                f"but you only have {mira}."
            )
            continue

        mira -= eq_def["price"]
        eq_inventory.append(build_equipment_entry(eq_def["id"], slot))
        await src_channel.send(
            f"Bought {eq_def['name']}! Mira remaining: {mira}"
        )

    return eq_inventory, mira


async def change_equipment(
    client_obj: Client,
    message_obj: Message,
    equipped: dict,
    eq_inventory: list[dict],
) -> tuple[dict, list[dict]]:
    """
    Equipment change menu. equipped is {"weapon": id|None, "armor": id|None, "accessory": id|None}.
    Returns (updated_equipped, updated_eq_inventory).
    """
    src_channel = message_obj.channel

    while True:
        weapon_def = get_equipment_def(equipped["weapon"]) if equipped["weapon"] else None
        armor_def = get_equipment_def(equipped["armor"]) if equipped["armor"] else None

        weapon_str = format_equipment_entry(weapon_def) if weapon_def else "(none)"
        armor_str = format_equipment_entry(armor_def) if armor_def else "(none)"

        await src_channel.send(
            "**Equipped**\n"
            f"1 - Weapon: {weapon_str}\n"
            f"2 - Armor:  {armor_str}\n"
            "0 - Back"
        )

        slot_choice = await wait_for_digit_reply(
            client_obj, message_obj.author, message_obj.channel
        )
        if slot_choice is None:
            await src_channel.send("You took too long!")
            break

        chosen_slot = int(slot_choice.content)
        if chosen_slot == 0:
            break
        if chosen_slot not in (1, 2):
            await src_channel.send("Please choose 1 (Weapon) or 2 (Armor).")
            continue

        slot_name = "weapon" if chosen_slot == 1 else "armor"
        slot_key = "weapons" if slot_name == "weapon" else "armors"

        # Show owned items for this slot
        owned_for_slot = [e for e in eq_inventory if e["slot"] == slot_name]
        if not owned_for_slot:
            await src_channel.send(f"You don't own any {slot_name}s yet! Visit the shop first.")
            continue

        lines = [f"**Choose a {slot_name}:**"]
        for i, entry in enumerate(owned_for_slot):
            eq_def = get_equipment_def(entry["id"])
            currently = " _(equipped)_" if entry["id"] == equipped[slot_name] else ""
            lines.append(f"{i + 1} - {format_equipment_entry(eq_def)}{currently}")
        lines.append("0 - Back")
        await src_channel.send("\n".join(lines))

        item_choice = await wait_for_digit_reply(
            client_obj, message_obj.author, message_obj.channel
        )
        if item_choice is None:
            await src_channel.send("You took too long!")
            break

        chosen_item = int(item_choice.content)
        if chosen_item == 0:
            continue
        if chosen_item > len(owned_for_slot):
            await src_channel.send(
                f"That's not a valid choice! Pick a number between 1 and {len(owned_for_slot)}."
            )
            continue

        new_id = owned_for_slot[chosen_item - 1]["id"]
        if new_id == equipped[slot_name]:
            await src_channel.send("That's already equipped!")
            continue

        equipped[slot_name] = new_id
        eq_def = get_equipment_def(new_id)
        await src_channel.send(f"Equipped {eq_def['name']}!")

    return equipped, eq_inventory