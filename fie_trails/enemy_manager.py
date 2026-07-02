import json
import os
from discord import Client, Message
from fie_trails.enemy import Enemy
from fie_trails.craft import Craft
import asyncio

ENEMIES_PATH = os.path.join(os.path.dirname(__file__), "data", "enemies.json")


def _load_all() -> list[dict]:
    with open(ENEMIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["bosses"]


def build_enemy(boss_data: dict) -> Enemy:
    """Construct an Enemy instance from a boss dict."""
    crafts = [
        Craft(
            c["name"],
            boss_data["str"] * c["damage_multiplier"],
            c["cost"],
        )
        for c in boss_data.get("crafts", [])
    ]
    return Enemy(
        boss_data["name"],
        boss_data["max_hp"],
        boss_data["max_hp"],   # current_HP starts at max
        boss_data["str"],
        boss_data["def"],
        boss_data["ats"],
        boss_data["adf"],
        boss_data["spd"],
        1,                     # level placeholder
        boss_data["xp_reward"],
        1,                     # mira placeholder
        boss_data.get("mira_reward", 0),
        crafts,
    )


async def select_boss(
    client_obj: Client,
    message_obj: Message,
    unlocked_bosses: list[str],
) -> tuple[Enemy, dict] | None:
    """
    Shows the player a menu of unlocked bosses and returns
    (Enemy, boss_dict) for the chosen one, or None on timeout.
    """
    src_channel = message_obj.channel
    all_bosses = _load_all()
    available = [b for b in all_bosses if b["id"] in unlocked_bosses]

    if not available:
        await src_channel.send("No bosses available yet!")
        return None

    lines = ["Choose your opponent:"]
    for i, boss in enumerate(available):
        lines.append(f"{i + 1} - {boss['name']}")
    await src_channel.send("\n".join(lines))

    def check(m):
        return (
            m.author == message_obj.author
            and m.channel == message_obj.channel
            and m.content.isdigit()
            and 1 <= int(m.content) <= len(available)
        )

    try:
        reply = await client_obj.wait_for("message", check=check, timeout=120.0)
    except asyncio.TimeoutError:
        await src_channel.send("You took too long to decide!")
        return None

    chosen = available[int(reply.content) - 1]
    return build_enemy(chosen), chosen