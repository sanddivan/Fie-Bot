import fieutils
from fie_trails.character import Character
from fie_trails.enemy import Enemy
from fie_trails.scraft import SCraft
from dataclasses import dataclass
import random
import asyncio
from fieemotes import emote
from discord import Client, Message

MAX_CP = 200
CP_ON_HIT = 10
CP_ON_HIT_RECEIVED = 5


@dataclass
class ActiveBuff:
    label: str        # displayed to the user, e.g. "+25% ATK"
    stat: str         # character attribute to boost, e.g. "str"
    multiplier: float # e.g. 1.25 for a 25% boost
    turns_left: int


async def wait_for_digit_reply(client, author, channel, timeout=120.0):
    """Waits for a numeric message from a specific user in a specific channel."""
    def check(m):
        return (
            m.author == author and
            m.channel == channel and
            m.content.isdigit()
        )
    try:
        return await client.wait_for("message", check=check, timeout=timeout)
    except asyncio.TimeoutError:
        return None


async def fight(
    client_obj: Client,
    message_obj: Message,
    character: Character,
    enemy: Enemy,
) -> None:
    src_channel = message_obj.channel

    # Start each fight with full CP and no active buffs
    character.cp = MAX_CP
    active_buffs: list[ActiveBuff] = []

    def gain_cp(amount: int):
        character.cp = min(MAX_CP, character.cp + amount)

    def get_buffed_stat(stat: str) -> int:
        """Return the character's stat with all active buffs applied."""
        base = getattr(character, stat)
        for buff in active_buffs:
            if buff.stat == stat:
                base = int(base * buff.multiplier)
        return base

    def apply_buff(new_buff: ActiveBuff):
        """Add a buff, or reset its duration if it's already active."""
        for buff in active_buffs:
            if buff.stat == new_buff.stat and buff.label == new_buff.label:
                buff.turns_left = new_buff.turns_left
                return
        active_buffs.append(new_buff)

    async def tick_buffs():
        """
        Decrement all buff durations by 1 after a character turn.
        Sends a message for any buff that just expired.
        """
        expired = [b for b in active_buffs if b.turns_left <= 1]
        for buff in expired:
            await src_channel.send(f"{buff.label} buff has worn off!")
        active_buffs[:] = [b for b in active_buffs if b.turns_left > 1]
        for buff in active_buffs:
            buff.turns_left -= 1

    def buffs_display() -> str:
        if not active_buffs:
            return ""
        parts = [f"{b.label} ({b.turns_left} turns left)" for b in active_buffs]
        return " | Buffs: " + ", ".join(parts)

    async def choose_craft(character: Character):
        while True:
            craft_list = []
            for i, craft in enumerate(character.crafts):
                entry = f"{i + 1} - {craft}"
                if craft.cost > character.cp:
                    entry = f"_{entry} (needs {craft.cost} CP)_"
                craft_list.append(entry)
            if character.s_crafts:
                for i, s_craft in enumerate(character.s_crafts):
                    idx = len(character.crafts) + i + 1
                    entry = f"{idx} - {s_craft}"
                    if s_craft.cost > character.cp:
                        entry = f"_{entry} (needs {s_craft.cost} CP)_"
                    craft_list.append(entry)

            craft_list.append("0 - Go back")
            await src_channel.send("\n".join(craft_list))

            craft_choice = await wait_for_digit_reply(
                client_obj, message_obj.author, message_obj.channel
            )

            if craft_choice is None:
                await src_channel.send(
                    f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
                )
                return None, "buff"

            craft_chosen = int(craft_choice.content)

            if craft_chosen == 0:
                return None, "back"

            num_crafts = len(character.crafts)
            total = num_crafts + len(character.s_crafts)

            if craft_chosen > total:
                await src_channel.send(
                    f"That's not a valid choice! Pick a number between 1 and {total}."
                )
                continue

            if craft_chosen <= num_crafts:
                selected = character.crafts[craft_chosen - 1]
            else:
                selected = character.s_crafts[craft_chosen - num_crafts - 1]

            if selected.cost > character.cp:
                await src_channel.send(
                    f"Not enough CP! You have {character.cp}/{MAX_CP}. Pick another craft."
                )
                continue

            character.cp -= selected.cost

            # Self-buff crafts have 0 multiplier
            if selected.multiplier == 0.0:
                if selected.name == "Motivate":
                    apply_buff(ActiveBuff(
                        label="+25% ATK",
                        stat="str",
                        multiplier=1.25,
                        turns_left=4,
                    ))
                    await src_channel.send("Rean steels himself! +25% ATK for 4 turns.")
                return 0, "buff"

            # Calculate damage from buffed STR at the moment of use
            damage = int(get_buffed_stat("str") * selected.multiplier)

            if isinstance(selected, SCraft):
                await src_channel.send("Aoki honoo yo...\n")
                await asyncio.sleep(1)
                await src_channel.send("Waga ken ni tsudoe!\n")
                await asyncio.sleep(1)
                await fieutils.send_file(
                    message_obj, "images/Rean_Schwarzer_S-Craft_Summer.png", False
                )
                await asyncio.sleep(0.5)
                await src_channel.send("Haaaaaaaa... zan!\n")
                await asyncio.sleep(2)

            return damage, "craft"

    async def choose_art(character: Character):
        while True:
            art_list = []
            for i, art in enumerate(character.equipped_arts):
                entry = f"{i + 1} - {art}"
                if art.cost > character.current_ep:
                    entry = f"_{entry} (needs {art.cost} EP)_"
                art_list.append(entry)

            art_list.append("0 - Go back")
            await src_channel.send("\n".join(art_list))

            art_choice = await wait_for_digit_reply(
                client_obj, message_obj.author, message_obj.channel
            )

            if art_choice is None:
                await src_channel.send(
                    f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
                )
                return None, "art"

            art_chosen = int(art_choice.content)

            if art_chosen == 0:
                return None, "back"

            if art_chosen > len(character.equipped_arts):
                await src_channel.send(
                    f"That's not a valid choice! Pick a number between 1 and {len(character.equipped_arts)}."
                )
                continue

            selected_art = character.equipped_arts[art_chosen - 1]

            if selected_art.cost > character.current_ep:
                await src_channel.send(
                    f"Not enough EP! You have {character.current_ep}/{character.ep}. "
                    f"Pick another art."
                )
                continue

            character.current_ep -= selected_art.cost
            return selected_art.damage + character.ats, "art"

    async def character_turn(character: Character):
        while True:
            await src_channel.send(
                f"CP: {character.cp}/{MAX_CP} | "
                f"EP: {character.current_ep}/{character.ep}"
                f"{buffs_display()}\n"
                "Choose an action\n"
                "1 - Normal Attack\n"
                "2 - Crafts\n"
                "3 - Arts\n"
                "4 - Items\n"
            )

            combat_choice = await wait_for_digit_reply(
                client_obj, message_obj.author, message_obj.channel
            )

            if combat_choice is None:
                await src_channel.send(
                    f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
                )
                return None, "physical"

            option = int(combat_choice.content)
            match option:
                case 1:
                    return get_buffed_stat("str"), "physical"
                case 2:
                    result = await choose_craft(character)
                    if result[1] == "back":
                        continue
                    return result
                case 3:
                    result = await choose_art(character)
                    if result[1] == "back":
                        continue
                    return result
                case 4:
                    return 0, "buff"
                case _:
                    await src_channel.send(
                        "Are you serious? All you have to do is choose between 1 and 4..."
                    )
                    continue

    async def enemy_turn(enemy: Enemy):
        choice = random.randint(0, len(enemy.crafts))

        if choice != 0:
            await src_channel.send(
                f"{enemy.get_name()} used {enemy.get_specific_craft(choice - 1)}\n"
            )
        else:
            await src_channel.send(f"{enemy.get_name()} used a normal attack!\n")
        await asyncio.sleep(1)

        if choice == 0:
            return enemy.STR
        else:
            enemy.set_cp(enemy.get_cp() - enemy.crafts[choice - 1].cost)
            return enemy.crafts[choice - 1].damage

    def reset_everyone(enemy: Enemy, character: Character):
        character.reset()
        enemy.reset()

    async def check_victory(enemy: Enemy, character: Character):
        if enemy.get_current_hp() <= 0:
            await src_channel.send("You won!\n")
            character.set_xp(character.current_xp + enemy.get_xp())
            await src_channel.send(f"XP gained: {enemy.get_xp()}")
            reset_everyone(enemy, character)
            return True
        return False

    async def check_defeat(character: Character, enemy: Enemy):
        if character.current_hp <= 0:
            await src_channel.send("You lost!\n")
            reset_everyone(enemy, character)
            return True
        return False

    def dif(difference: int) -> int:
        return max(0, difference)

    async def resolve_character_action(damage_dealt, damage_type):
        """Apply damage and CP gain for a character action."""
        if damage_type == "buff":
            return
        elif damage_type == "art":
            difference = dif(damage_dealt - enemy.get_adf())
        else:  # "physical" or "craft"
            difference = dif(damage_dealt - enemy.get_def())

        enemy.set_current_hp(enemy.get_current_hp() - difference)
        gain_cp(CP_ON_HIT)
        await src_channel.send(
            f"Enemy HP: {enemy.get_current_hp()} (-{difference})\n"
        )
        await asyncio.sleep(1)

    async def start_fight(character: Character, enemy: Enemy):
        while character.current_hp > 0 and enemy.current_HP > 0:
            if character.spd >= enemy.SPD:
                damage_dealt, damage_type = await character_turn(character)
                await tick_buffs()
                await resolve_character_action(damage_dealt, damage_type)

                if await check_victory(enemy, character):
                    return

                damage_received = await enemy_turn(enemy)
                difference = dif(damage_received - character.dfs)
                character.current_hp -= difference
                gain_cp(CP_ON_HIT_RECEIVED)
                await src_channel.send(
                    f"Character HP: {character.current_hp} (-{difference})\n"
                )
                await asyncio.sleep(1)

                if await check_defeat(character, enemy):
                    return

            else:
                damage_received = await enemy_turn(enemy)
                difference = dif(damage_received - character.dfs)
                character.current_hp -= difference
                gain_cp(CP_ON_HIT_RECEIVED)
                await src_channel.send(
                    f"Character HP: {character.current_hp} (-{difference})\n"
                )
                await asyncio.sleep(1)

                if await check_defeat(character, enemy):
                    return

                damage_dealt, damage_type = await character_turn(character)
                await tick_buffs()
                await resolve_character_action(damage_dealt, damage_type)

                if await check_victory(enemy, character):
                    return

        await check_victory(enemy, character)
        await check_defeat(character, enemy)

    await start_fight(character, enemy)