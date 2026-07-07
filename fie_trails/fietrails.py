from discord import Client, Message
from fie_trails.customization import change_orbments
from fie_trails import user_manager, enemy_manager, orbment_manager, item_manager
from fie_trails.combat import fight
from fieemotes import emote
import asyncio
import fieutils


async def wait_for_digit_reply(client, author, channel, timeout=120.0):
    """Waits for a numeric message from a specific user in a specific channel."""
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


async def fie_trails(client_obj: Client, message_obj: Message):
    src_channel = message_obj.channel
    user_id = message_obj.author.id

    character, unlocked_bosses, inventory = user_manager.load(user_id)

    while True:
        await src_channel.send(
            "What do you want to do?\n"
            "1 - Fight\n"
            "2 - Change Equipment\n"
            "3 - Change Orbments\n"
            "4 - Check status\n"
            "5 - Shop\n"
            "0 - Quit\n"
        )

        menu_choice = await wait_for_digit_reply(
            client_obj,
            message_obj.author,
            message_obj.channel,
            timeout=120.0,
        )

        if menu_choice is None:
            await src_channel.send(
                f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
            )
            return

        option = int(menu_choice.content)
        match option:
            case 1:
                result = await enemy_manager.select_boss(
                    client_obj, message_obj, unlocked_bosses
                )
                if result is None:
                    continue

                enemy, boss_data = result
                await fight(client_obj, message_obj, character, enemy, inventory)

                if character.current_hp > 0:
                    # Unlock next boss
                    unlocked_bosses = user_manager.unlock_next_boss(
                        unlocked_bosses, boss_data
                    )

                    # Award mira
                    character.mira += boss_data.get("mira_reward", 0)
                    await src_channel.send(
                        f"Mira obtained: {boss_data.get('mira_reward', 0)} "
                        f"(Total: {character.mira})"
                    )

                    # Roll and award orbment drops
                    dropped_ids = orbment_manager.roll_drops(boss_data)
                    new_orbments = user_manager.add_orbment_drops(
                        user_id, character, unlocked_bosses, dropped_ids
                    )
                    if new_orbments:
                        names = ", ".join(new_orbments)
                        await src_channel.send(f"Orbment obtained: {names}!")

                user_manager.save(user_id, character, unlocked_bosses, inventory)

            case 2:
                await src_channel.send("Work in progress!")

            case 3:
                await change_orbments(client_obj, message_obj, character)
                user_manager.save(user_id, character, unlocked_bosses, inventory)

            case 4:
                await fieutils.send_file(message_obj, "images/Rean_Menu_CSI.png", False)
                await src_channel.send(character.status())

            case 5:
                inventory, _ = await item_manager.show_shop(
                    client_obj, message_obj, character, inventory, unlocked_bosses
                )
                user_manager.save(user_id, character, unlocked_bosses, inventory)

            case 0:
                await src_channel.send(f"Until next time! {emote('WAVE')}\n")
                return

            case _:
                await src_channel.send(
                    "Are you serious? All you have to do is choose between 0 and 5...\n"
                )