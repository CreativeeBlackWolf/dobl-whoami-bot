import discord
from multipledispatch import dispatch
import mapparser
import player

@dispatch(discord.Message, player.Player)
async def send_inventory(message: discord.Message, player: player.Player) -> None:
    """
    Send inventory of a given player
    """
    inv = "\n".join(player.inventory)
    await message.channel.send(f'''```ansi
Инвентарь:
{inv}
```''')

@dispatch(discord.Message, list)
async def send_inventory(message: discord.Message, inventory: list, format = True) -> None:
    """
    Format inventory list
    """
    inv = "\n".join(player.Player.format_inventory_list(inventory) if format else inventory)
    await message.delete()
    await message.channel.send(f'''```ansi
Инвентарь:
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

def get_player_info(map: mapparser.Map, player: player.Player):
    return f'''```
ОЗ: {player.format_HP()}
ОМ: {player.format_MP()}
ОД: {player.SP}
УР: {player.level}
ФРА: {player.frags}
Рероллы: {player.rerolls}

Персонаж актуален на момент времени: {map.map_datetime}.
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