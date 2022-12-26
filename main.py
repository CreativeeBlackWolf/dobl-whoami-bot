#!/usr/bin/env python3
import configparser
import discord
import mapparser
import help
import asyncio


config = configparser.ConfigParser()
config.read('botconfig.cfg')
prefix = config.get("bot", "prefix")

intents = discord.Intents.default()
intents.message_content = True


client = discord.Client(intents=intents)

async def send_inventory(message, player) -> None:
    inv = "\n".join(player.inventory)
    await message.channel.send(f'''```
Инвентарь:
{inv}
```''')

async def send_abilities(message, player) -> None:
    active = "\n".join(player.active_abilities)
    passive = "\n".join(player.passive_abilities)
    await message.channel.send(f'''```
Навыки:
{active}

Особенности:
{passive})
```''')


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="напиши .помоги"))


@client.event
async def on_message(message):
    if message.author == client.user:
        return


    if message.content.lower().startswith(prefix + "помоги"):
        await message.channel.send(help.get_commands())

    if message.content.lower().startswith(prefix + 'кто я'):
        map = mapparser.Map(config["map"]["path"])
        player = map.get_player(message.author.display_name)

        if not player:
            await message.channel.send("Ты не существуешь.")
            return

        msg = await message.channel.send(f'''```
ОЗ: {player.HP}
ОМ: {player.MP}
ОД: {player.SP}
УР: {player.level}
ФРА: {player.frags}
Рероллы: {player.rerolls}

Если хочешь увидеть инвентарь, нажми на 📦, или введи `{prefix}покажи инвентарь`
Если хочешь увидеть навыки и особенности, нажми на 🔸, или введи `{prefix}покажи навыки`

Персонаж актуален на момент времени: {map.map_datetime}.
Учитывай, что данные за время могли измениться.
```''')

        await msg.add_reaction("📦")
        await msg.add_reaction("🔸")

        try:
            reaction, user = await client.wait_for("reaction_add", check = lambda reaction, user: True if user == message.author and
                                                                           str(reaction.emoji) in ["📦", "🔸"]
                                                                           else False, timeout = 10)
        except asyncio.TimeoutError:
            await msg.remove_reaction("📦", client.user)
            await msg.remove_reaction("🔸", client.user)
        else:
            if str(reaction.emoji) == "📦":
                await send_inventory(message, player)
            elif str(reaction.emoji) == "🔸":
                await send_abilities(message, player)

    if message.content.lower().startswith(prefix + 'покажи'):
        map = mapparser.Map(config["map"]["path"])
        player = map.get_player(message.author.display_name)

        if not player:
            await message.channel.send("Ты не существуешь.")
            return

        args = message.content.lower().split()
        if len(args) == 2:
            if args[1] in ["скиллы", "способности", "особенности", "навыки", "спеллы"]:
                await send_abilities(message, player)
            elif args[1] in ["инвентарь", "шмотки"]:
                await send_inventory(message, player)
            else:
                await message.channel.send(f'Неправильное использование команды:\n{help.get_commands("покажи")}')
        else:
            await message.channel.send(f'Неправильное использование команды:\n{help.get_commands("покажи")}')
    
    if message.content.lower().startswith(prefix + 'где я'):
        map = mapparser.Map(config["map"]["path"])
        player = map.get_player(message.author.display_name)

        if not player:
            await message.channel.send("Ты не существуешь.")
            return
        
        resp = map.construct_ascii_repr(player)
        await message.reply('```ansi\n'+resp+'\n```')


if __name__ == '__main__':
    bot_token = config['bot']['token']
    client.run(bot_token)
