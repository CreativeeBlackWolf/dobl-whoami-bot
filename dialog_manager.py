import re
from typing import Union
import discord
import mapparser
import player
from config import Config


async def send_player_inventory(message: discord.Message, player: player.Player) -> None:
    """
    Send inventory of a given player
    """
    inv = "\n".join(player.inventory)
    await message.channel.send(f'''```ansi
Инвентарь:
{inv}
```''')

async def send_formatted_inventory(message: discord.Message, inventory: list, formatInventory = True) -> None:
    """
    Format inventory list
    """
    inv = "\n".join(player.Player.format_inventory_list(inventory) if formatInventory else inventory)
    await message.delete()
    await message.channel.send(f'''```ansi
{inv}
```''')

async def send_abilities(message: discord.Message, player: player.Player) -> None:
    active = "\n".join(player.active_abilities)
    passive = "\n".join(player.passive_abilities)
    await message.channel.send(f'''```
Навыки:
{active}

Особенности:
{passive}
```''')

def get_inventory_string(player: player.Player):
    inv = "\n".join(player.inventory)
    return f'''```ansi
Инвентарь:
{inv}
```'''

def get_player_info_string(gameMap: mapparser.Map, player: player.Player):
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

def get_abilities_string(player: player.Player):
    active = "\n".join(player.active_abilities)
    passive = "\n".join(player.passive_abilities)
    return f'''```
Навыки:
{active}

Особенности:
{passive}
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
        unicode_emoji: list[str] = re.findall(r"[\U00010000-\U0010ffff]", message.content)
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

    config.Bot.set_reaction_trigger(
        reaction_message_id=message.reference.message_id if append else reaction_message.id,
        reaction_emoji=reaction_emoji.id if reaction_emoji else unicode_emoji,
        reaction_role_id=reaction_role.id,
        message_on_reaction=message_on_reaction
    )
    config.Bot.write_reaction_triggers_file()
