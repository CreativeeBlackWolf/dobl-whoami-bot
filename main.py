#!/usr/bin/env python3
import configparser
import discord
import asyncio
import re
from dialog_manager import send_abilities, send_inventory
import mapparser
import command_help


config = configparser.ConfigParser()
config.read('botconfig.cfg')
prefix = config.get("bot", "prefix", fallback=".")
admins = config.get("bot", "admins", fallback="")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="напиши .помоги"))


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return


    if message.content.lower().startswith(prefix + "помоги"):
        splittedMessage = message.content.split()
        if len(splittedMessage) == 1:
            await message.channel.send(command_help.get_commands())
        elif len(splittedMessage) >= 2:
            if splittedMessage[1] == "мне":
                await message.channel.send("Сам справишься.")
            else:
                await message.channel.send(command_help.get_commands(" ".join(splittedMessage[1::])))

    if message.content.lower().startswith((prefix + 'кто я', prefix + 'я кто')):
        map = mapparser.Map(config["map"]["path"])
        player = map.get_player(message.author.display_name, message.author.id)

        if player == mapparser.MapObjectError.NOT_FOUND:
            await message.channel.send("Ты не существуешь.")
            return
        elif player == mapparser.MapObjectError.WRONG_ID:
            await message.channel.send("Ты меня обмануть пытаешься?")
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

        servedInv, servedAbils = False, False
        while True:
            try:
                reaction, user = await client.wait_for(
                    "reaction_add", 
                    check = lambda reaction, user: True if user == message.author and
                                                        str(reaction.emoji) in ["📦", "🔸"] and
                                                        reaction.message == msg
                                                        else False, timeout = 10)
            except asyncio.TimeoutError:
                await msg.remove_reaction("📦", client.user)
                await msg.remove_reaction("🔸", client.user)
                break
            else:
                if not servedInv and str(reaction.emoji) == "📦":
                    await send_inventory(message, player)
                    await msg.remove_reaction("📦", client.user)
                    servedInv = True
                elif not servedAbils and str(reaction.emoji) == "🔸":
                    await send_abilities(message, player)
                    await msg.remove_reaction("🔸", client.user)
                    servedAbils = True

    if message.content.lower().startswith(prefix + 'покажи'):
        map = mapparser.Map(config["map"]["path"])
        player = map.get_player(message.author.display_name, message.author.id)

        if player == mapparser.MapObjectError.NOT_FOUND:
            await message.channel.send("Ты не существуешь.")
            return
        elif player == mapparser.MapObjectError.WRONG_ID:
            await message.channel.send("Ты меня обмануть пытаешься?")
            return

        args = message.content.lower().split()
        if len(args) == 2:
            if args[1] in ["скиллы", "способности", "особенности", "навыки", "спеллы", "абилки"]:
                await send_abilities(message, player)
            elif args[1] in ["инвентарь", "шмотки"]:
                await send_inventory(message, player)
            else:
                await message.channel.send(f'Неправильное использование команды:\n{command_help.get_commands("покажи")}')
        else:
            await message.channel.send(f'Неправильное использование команды:\n{command_help.get_commands("покажи")}')
    
    if message.content.lower().startswith(prefix + 'где я'):
        map = mapparser.Map(config["map"]["path"])
        player = map.get_player(message.author.display_name, message.author.id)

        if player == mapparser.MapObjectError.NOT_FOUND:
            await message.channel.send("Ты не существуешь.")
            return
        elif player == mapparser.MapObjectError.WRONG_ID:
            await message.channel.send("Ты меня обмануть пытаешься?")
            return

        resp = '```ansi\n'+map.construct_ascii_repr(player)+'\n```\n'+map.list_doors_string(player)
        await message.reply(resp)

    if message.content.lower().startswith(".группа"):
        groupRole: discord.Role = None
        for role in message.author.roles:
            if role.name.startswith("группа"):
                groupRole = role
                break
        else:
            await message.channel.send("Ты не находишься в группе.")
            return

        map = mapparser.Map(config["map"]["path"])
        groupMembers = list(groupRole.members)
        msg = "```ansi\n"
        for member in groupMembers:
            player = map.get_player(member.display_name, member.id)
            msg += f"{member.display_name}: <[31m{player.HP.split()[0]}[0m> <[34m{player.MP.split()[0]}[0m>\n"

        msg += "\n```"
        await message.channel.send(msg)

    if message.content.lower().startswith('.инвентарь'):
        if str(message.author.id) not in admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        if len(message.content.split("\n")) < 2:
            if len(message.content.split()) >= 2:
                map = mapparser.Map(config["map"]["path"])
                inv = map.get_objects_inventory(" ".join(message.content.split()[1::]))
                
                if inv is mapparser.MapObjectError.NOT_FOUND:
                    await message.channel.send("Объекта с таким именем нет на карте.")
                    return

                await send_inventory(message, inv, format=False)
                return

            await message.channel.send("А инвентарь-то где?")
            return

        await send_inventory(message, message.content.split("\n")[1::])


if __name__ == '__main__':
    bot_token = config['bot']['token']
    client.run(bot_token)
