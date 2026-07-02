import asyncio
from discord import Client, Message
from fie_trails.character import Character
from fieemotes import emote

SLOTS = 6


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


async def change_orbments(
    client_obj: Client, message_obj: Message, character: Character
) -> None:
    src_channel = message_obj.channel

    # Show equipped slots (None slots shown as empty)
    slot_lines = []
    for i, slot in enumerate(character.equipped_orbments):
        label = str(slot) if slot is not None else "(empty)"
        slot_lines.append(f"{i + 1} - {label}")
    slot_lines.append("0 - Exit")

    await src_channel.send("Equipped orbments:\n" + "\n".join(slot_lines))

    slot_choice = await wait_for_digit_reply(
        client_obj, message_obj.author, message_obj.channel
    )

    if slot_choice is None:
        await src_channel.send(
            f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
        )
        return

    slot_chosen = int(slot_choice.content)
    if slot_chosen == 0:
        return
    if slot_chosen > SLOTS:
        await src_channel.send("That's not an available slot!")
        return

    # Show available orbments
    if not character.available_orbments:
        await src_channel.send("You don't have any orbments to equip yet!")
        return

    available_lines = []
    for i, orb in enumerate(character.available_orbments):
        available_lines.append(f"{i + 1} - {orb}")
    available_lines.append("0 - Unequip slot")

    await src_channel.send("Available orbments:\n" + "\n".join(available_lines))

    replacement_choice = await wait_for_digit_reply(
        client_obj, message_obj.author, message_obj.channel
    )

    if replacement_choice is None:
        await src_channel.send(
            f"You took too long to decide! I'm going to sleep {emote('SLEEP')}"
        )
        return

    available_chosen = int(replacement_choice.content)

    if available_chosen == 0:
        # Unequip: move equipped orbment back to available if there was one
        current = character.equipped_orbments[slot_chosen - 1]
        if current is not None:
            character.available_orbments.append(current)
        character.equipped_orbments[slot_chosen - 1] = None
        await src_channel.send(f"Slot {slot_chosen} unequipped.")
    else:
        if available_chosen > len(character.available_orbments):
            await src_channel.send("That's not a valid orbment!")
            return

        incoming = character.available_orbments[available_chosen - 1]
        outgoing = character.equipped_orbments[slot_chosen - 1]

        # Swap: put the previously equipped orbment back into available
        character.available_orbments[available_chosen - 1] = outgoing if outgoing is not None else incoming
        if outgoing is None:
            character.available_orbments.pop(available_chosen - 1)
        character.equipped_orbments[slot_chosen - 1] = incoming

        await src_channel.send(
            f"Equipped {incoming} in slot {slot_chosen}."
            + (f" {outgoing} moved to inventory." if outgoing else "")
        )

    # Immediately refresh arts so the new orbment takes effect
    character.refresh_equipped_arts()


async def change_equipment(
    client_obj: Client, message_obj: Message, character: Character
) -> None:
    # WIP
    pass