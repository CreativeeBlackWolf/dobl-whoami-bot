import re
from typing import Union
import discord
import mapparser
from player import Player
from config import Config


def get_inventory_string(player: Player):
    inv = "\n".join(player.inventory)
    return f'''```ansi
Инвентарь:
{inv}
```'''

def get_player_info_string(gameMap: mapparser.Map, player: Player):
    return f'''```
ОЗ: {player.format_HP()}
ОМ: {player.format_MP()}
ОД: {player.SP}
УР: {player.level}
ФРА: {player.frags}
Рероллы: {player.rerolls}

Персонаж актуален на момент времени: {gameMap.map_datetime}.
Учитывай, что данные за время могли измениться.
```'''

def get_abilities_string(player: Player):
    active = "\n".join(player.active_abilities)
    passive = "\n".join(player.passive_abilities)
    return f'''```
Навыки:
{active}

Особенности:
{passive}
```'''

def get_formatted_inventory(
        inventory: list,
        format_inventory: bool = True,
        show_equipped_only: bool = False) -> str:
    inv = "\n".join(Player.format_inventory_list(inventory, show_equipped_only) if format_inventory else inventory)
    return f'''```ansi
{inv}
```'''

def get_player_position_string(game_map: mapparser.Map, player: Player) -> str:
    return f'''```ansi
{game_map.get_floor_string(player)}

{game_map.construct_ascii_room(player)}

{game_map.list_doors_string(player)}
```'''

async def add_reaction_message(
    message: Union[discord.Message, discord.MessageReference],
    config: Config,
    append: bool = False,) -> bool:

    await message.delete()

    args = message.content.split()
    if append and not message.reference:
        await message.channel.send("Ты должен ответить на сообщение, к которому хочешь привязать уведомления")
        return False

    reaction_role = message.role_mentions[0] if message.role_mentions else None
    if reaction_role is None:
        await message.channel.send("Упомяни роль, которую хочешь присваивать.")
        return False

    reaction_emoji = re.findall(r"<:\w*:(\d*)>", message.content)
    if not reaction_emoji:
        unicode_emoji: list[str] = re.findall(r"[\u263a-\U0001ffff]", message.content)
        if not unicode_emoji:
            await message.channel.send("Напиши эмоцию, на которую будут люди реагировать.")
            return False
        unicode_emoji = unicode_emoji[0]

    if len(args) <= 4:
        await message.channel.send("Напиши сообщение, которое нужно отправлять при подписке и отписке через `/`.")
        return False

    if not append and len(message.content.split("\n")) == 1:
        await message.channel.send("Напиши, что ты хочешь увидеть в сообщении (с новой строки).")
        return False

    message_on_reaction = " ".join(message.content.split("\n")[0].split()[4::])

    if len(message_on_reaction.split("/")) == 1:
        await message.channel.send("Ты должен написать сообщение об отписке через `/`")
        return False

    if not append:
        msg = "\n".join(message.content.split("\n")[1:])
        reaction_message = await message.channel.send(msg)

    if reaction_emoji:
        reaction_emoji: discord.Emoji = await message.guild.fetch_emoji(int(reaction_emoji[0]))

    if not append:
        await reaction_message.add_reaction(reaction_emoji or unicode_emoji)
    else:
        reference_message = await message.channel.fetch_message(message.reference.message_id)
        await reference_message.add_reaction(reaction_emoji or unicode_emoji)

    config.BotConfig.set_reaction_trigger(
        reaction_message_id=message.reference.message_id if append else reaction_message.id,
        reaction_emoji=reaction_emoji.id if reaction_emoji else unicode_emoji,
        reaction_role_id=reaction_role.id,
        message_on_reaction=message_on_reaction
    )
    config.BotConfig.write_reaction_triggers_file()

async def send_player_inventory(message: discord.Message, player: Player) -> None:
    """
    Send inventory of a given player
    """
    inventory_str = get_inventory_string(player)

    if len(inventory_str) >= 2000:
        inv_first = "\n".join(player.inventory[:len(player.inventory)])
        inv_second = "\n".join(player.inventory[len(player.inventory) + 1:])
        await message.channel.send(f"```ansi\n{inv_first}```")
        await message.channel.send(f"```ansi\n{inv_second}```")
    else:
        await message.channel.send(inventory_str)

async def send_formatted_inventory(
    message: discord.Message,
    inventory: list,
    format_inventory: bool = True,
    show_equipped_only: bool = False) -> None:
    """
    Format inventory list and send it to channel

    :param message: discord.Message object
    :param inventory: Player.inventory list
    :param format_inventory: format inventory with Player.format_inventory_list method
    :param show_equipped_only: see Player.format_inventory_list method parameters
    """
    await message.delete()
    await message.channel.send(
        get_formatted_inventory(inventory, format_inventory, show_equipped_only)
    )

async def send_abilities(message: discord.Message, player: Player) -> None:
    abilities_str = get_abilities_string(player)

    if len(abilities_str) >= 2000:
        active = "\n".join(player.active_abilities)
        passive = "\n".join(player.passive_abilities)
        await message.channel.send(f"```Навыки:\n{active}```")
        await message.channel.send(f"```Особенности:\n{passive}```")
    else:
        await message.channel.send(abilities_str)
