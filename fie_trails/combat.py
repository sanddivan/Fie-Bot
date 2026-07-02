import fieutils
from fie_trails.character import Character
from fie_trails.enemy import Enemy
from fie_trails.scraft import SCraft
import random
import asyncio
from fieemotes import emote
from discord import Client, Message


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

    async def choose_craft(character: Character):
        craft_list = []
        for i, craft in enumerate(character.crafts):
            craft_list.append(f"{i + 1} - {craft}")
        if character.s_crafts:
            for i, s_craft in enumerate(character.s_crafts):
                craft_list.append(f"{len(character.crafts) + i + 1} - {s_craft}")
        await src_channel.send("\n".join(craft_list))

        craft_choice = await wait_for_digit_reply(
            client_obj, message_obj.author, message_obj.channel
        )

        if craft_choice is None:
            await src_channel.send(
                f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
            )
            return None

        craft_chosen = int(craft_choice.content)
        num_crafts = len(character.crafts)

        if craft_chosen <= num_crafts:
            selected = character.crafts[craft_chosen - 1]
        else:
            selected = character.s_crafts[craft_chosen - num_crafts - 1]

        character.cp -= selected.cost

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

        return selected.damage

    async def choose_art(character: Character):
        art_list = []
        for i, art in enumerate(character.equipped_arts):
            art_list.append(f"{i + 1} - {art}")
        await src_channel.send("\n".join(art_list))

        art_choice = await wait_for_digit_reply(
            client_obj, message_obj.author, message_obj.channel
        )

        if art_choice is None:
            await src_channel.send(
                f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
            )
            return None

        art_chosen = int(art_choice.content)
        character.ep -= character.equipped_arts[art_chosen - 1].cost
        return character.equipped_arts[art_chosen - 1].damage

    async def character_turn(character: Character):
        await src_channel.send(
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
            return None

        option = int(combat_choice.content)
        match option:
            case 1:
                return character.str
            case 2:
                return await choose_craft(character)
            case 3:
                return await choose_art(character)
            case 4:
                return 0
            case _:
                await src_channel.send(
                    "Are you serious? All you have to do is choose between 1 and 4..."
                )
                return 0

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
            enemy.setCP(enemy.getCP() - enemy.crafts[choice - 1].cost)
            return enemy.crafts[choice - 1].damage

    def reset_everyone(enemy: Enemy, character: Character):
        character.reset()
        enemy.reset()

    async def check_victory(enemy: Enemy, character: Character):
        if enemy.get_current_HP() <= 0:
            await src_channel.send("You won!\n")
            character.set_xp(character.current_xp + enemy.getXP())
            await src_channel.send(f"XP gained: {enemy.getXP()}")
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

    async def start_fight(character: Character, enemy: Enemy):
        while character.current_hp > 0 and enemy.current_HP > 0:
            if character.spd >= enemy.SPD:
                difference = dif(await character_turn(character) - enemy.getDEF())
                enemy.set_current_HP(enemy.get_current_HP() - difference)
                await src_channel.send(
                    f"Enemy HP: {enemy.get_current_HP()} (-{difference})\n"
                )
                await asyncio.sleep(1)

                if await check_victory(enemy, character):
                    return

                difference = dif(await enemy_turn(enemy) - character.dfs)
                character.current_hp -= difference
                await src_channel.send(
                    f"Character HP: {character.current_hp} (-{difference})\n"
                )
                await asyncio.sleep(1)

                if await check_defeat(character, enemy):
                    return

            else:
                difference = dif(await enemy_turn(enemy) - character.dfs)
                character.current_hp -= difference
                await src_channel.send(
                    f"Character HP: {character.current_hp} (-{difference})\n"
                )
                await asyncio.sleep(1)

                if await check_defeat(character, enemy):
                    return

                difference = dif(await character_turn(character) - enemy.getDEF())
                enemy.set_current_HP(enemy.get_current_HP() - difference)
                await src_channel.send(
                    f"Enemy HP: {enemy.get_current_HP()} (-{difference})\n"
                )
                await asyncio.sleep(1)

                if await check_victory(enemy, character):
                    return

        await check_victory(enemy, character)
        await check_defeat(character, enemy)

    await start_fight(character, enemy)