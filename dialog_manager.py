import discord
import player
from multipledispatch import dispatch

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
    inv = "\n".join(player.Player.format_inventory(inventory) if format else inventory)
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
