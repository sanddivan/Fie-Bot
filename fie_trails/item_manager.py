import json
import os
from fie_trails.character import Character
from discord import Client, Message
import asyncio

ITEMS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "items.json")
MAX_STACK = 99


def _load_all() -> dict[str, dict]:
    """Returns all item definitions keyed by id."""
    with open(ITEMS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["id"]: item for item in data["items"]}


def get_available_items(unlocked_bosses: list[str]) -> list[dict]:
    """Return items available in the shop based on unlocked bosses."""
    all_items = _load_all()
    return [
        item for item in all_items.values()
        if item["unlocked_by"] is None or item["unlocked_by"] in unlocked_bosses
    ]


def resolve_inventory(inventory: list[dict]) -> list[dict]:
    """
    Validate inventory entries against the master item list.
    Returns only entries whose IDs still exist in items.json.
    """
    all_items = _load_all()
    return [
        entry for entry in inventory
        if entry["id"] in all_items
    ]


def get_item_def(item_id: str) -> dict | None:
    """Return a single item definition by ID."""
    return _load_all().get(item_id)


def add_to_inventory(
    inventory: list[dict], item_id: str, quantity: int
) -> tuple[list[dict], int]:
    """
    Add items to inventory, respecting MAX_STACK.
    Returns (updated_inventory, actually_added).
    """
    for entry in inventory:
        if entry["id"] == item_id:
            space = MAX_STACK - entry["quantity"]
            added = min(quantity, space)
            entry["quantity"] += added
            return inventory, added

    # Item not in inventory yet
    added = min(quantity, MAX_STACK)
    inventory.append({"id": item_id, "quantity": added})
    return inventory, added


def remove_from_inventory(
    inventory: list[dict], item_id: str, quantity: int = 1
) -> list[dict]:
    """Remove quantity of an item. Removes the entry entirely if it hits 0."""
    for entry in inventory:
        if entry["id"] == item_id:
            entry["quantity"] -= quantity
            break
    return [e for e in inventory if e["quantity"] > 0]


def apply_item(character: Character, item_def: dict) -> str:
    """
    Apply an item's effect to the character.
    Returns a message describing what happened.
    """
    effect = item_def["effect"]
    power = item_def["power"]
    name = item_def["name"]

    if effect == "heal_hp":
        amount = int(character.max_hp * power)
        old_hp = character.current_hp
        character.current_hp = min(character.max_hp, character.current_hp + amount)
        healed = character.current_hp - old_hp
        return f"Used {name}! Restored {healed} HP. (HP: {character.current_hp}/{character.max_hp})"

    elif effect == "heal_ep":
        amount = int(character.ep * power)
        old_ep = character.current_ep
        character.current_ep = min(character.ep, character.current_ep + amount)
        restored = character.current_ep - old_ep
        return f"Used {name}! Restored {restored} EP. (EP: {character.current_ep}/{character.ep})"

    return f"Used {name}, but nothing happened."


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


async def show_shop(
    client_obj: Client,
    message_obj: Message,
    character: Character,
    inventory: list[dict],
    unlocked_bosses: list[str],
) -> tuple[list[dict], int]:
    """
    Show the shop menu. Returns (updated_inventory, updated_mira).
    """
    src_channel = message_obj.channel
    available = get_available_items(unlocked_bosses)
    mira = character.mira

    while True:
        lines = [f"**Shop** — You have {mira} mira\n"]
        for i, item in enumerate(available):
            lines.append(f"{i + 1} - {item['name']} ({item['price']} mira) — {item['description']}")
        lines.append("0 - Leave shop")
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

        if chosen > len(available):
            await src_channel.send(
                f"That's not a valid choice! Pick a number between 1 and {len(available)}."
            )
            continue

        item = available[chosen - 1]

        # Ask for quantity
        await src_channel.send(
            f"How many **{item['name']}** would you like? "
            f"({item['price']} mira each)\n"
            f"You can afford up to {mira // item['price']}. Enter 0 to cancel."
        )

        qty_reply = await wait_for_digit_reply(
            client_obj, message_obj.author, message_obj.channel
        )
        if qty_reply is None:
            await src_channel.send("You took too long! Leaving the shop.")
            break

        qty = int(qty_reply.content)
        if qty == 0:
            continue

        total_cost = item["price"] * qty
        if total_cost > mira:
            await src_channel.send(
                f"Not enough mira! That would cost {total_cost} mira "
                f"but you only have {mira}."
            )
            continue

        inventory, added = add_to_inventory(inventory, item["id"], qty)
        if added < qty:
            await src_channel.send(
                f"You can only carry {MAX_STACK} of each item — "
                f"bought {added} {item['name']} instead."
            )
        actual_cost = item["price"] * added
        mira -= actual_cost
        character.mira = mira
        await src_channel.send(
            f"Bought {added}x {item['name']} for {actual_cost} mira. "
            f"Mira remaining: {mira}"
        )

    return inventory, mira


async def show_inventory_in_combat(
    client_obj: Client,
    message_obj: Message,
    character: Character,
    inventory: list[dict],
) -> tuple[list[dict], str]:
    """
    Show the item menu during combat.
    Returns (updated_inventory, result_message | "back" | "empty").
    """
    src_channel = message_obj.channel
    all_items = _load_all()

    usable = [e for e in inventory if e["quantity"] > 0 and e["id"] in all_items]

    if not usable:
        await src_channel.send("You have no items!")
        return inventory, "empty"

    while True:
        lines = []
        for i, entry in enumerate(usable):
            item_def = all_items[entry["id"]]
            lines.append(
                f"{i + 1} - {item_def['name']} x{entry['quantity']} "
                f"— {item_def['description']}"
            )
        lines.append("0 - Go back")
        await src_channel.send("\n".join(lines))

        choice = await wait_for_digit_reply(
            client_obj, message_obj.author, message_obj.channel
        )
        if choice is None:
            await src_channel.send("You took too long!")
            return inventory, "back"

        chosen = int(choice.content)
        if chosen == 0:
            return inventory, "back"

        if chosen > len(usable):
            await src_channel.send(
                f"That's not a valid choice! Pick a number between 1 and {len(usable)}."
            )
            continue

        entry = usable[chosen - 1]
        item_def = all_items[entry["id"]]
        result_msg = apply_item(character, item_def)
        inventory = remove_from_inventory(inventory, entry["id"])
        return inventory, result_msg