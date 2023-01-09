import discord
import mapparser
import player

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