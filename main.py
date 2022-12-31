#!/usr/bin/env python3
import discord
import asyncio
import random
from dialog_manager import send_abilities, send_inventory
from config import Config
import mapparser
import command_help


config = Config("botconfig.cfg")
intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="напиши .помоги"))


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return


    if message.content.lower().startswith(config.Bot.prefix + "помоги"):
        map = mapparser.Map(config.Map.path)
        player = map.get_player(message.author.display_name, message.author.id)

        splittedMessage = message.content.split()
        if len(splittedMessage) == 1:
            await message.channel.send(command_help.get_commands(player=player))
        elif len(splittedMessage) >= 2:
            if splittedMessage[1] == "мне":
                await message.channel.send("Сам справишься.")
            elif splittedMessage[1] == "админу":
                if str(message.author.id) in config.Bot.admins:
                    await message.channel.send(command_help.get_admin_command())
                else:
                    await message.channel.send("Ты кто вообще такой?")
            else:
                await message.channel.send(command_help.get_commands(" ".join(splittedMessage[1::]), player))

    elif message.content.lower().startswith((config.Bot.prefix + 'кто я', config.Bot.prefix + 'я кто')):
        map = mapparser.Map(config.Map.path)
        player = map.get_player(message.author.display_name, message.author.id)

        if player == mapparser.MapObjectError.NOT_FOUND:
            await message.channel.send("Ты не существуешь.")
            return
        elif player == mapparser.MapObjectError.WRONG_ID:
            await message.channel.send("Ты меня обмануть пытаешься?")
            return

        msg = await message.channel.send(f'''```
ОЗ: {player.format_HP()}
ОМ: {player.format_MP()}
ОД: {player.SP}
УР: {player.level}
ФРА: {player.frags}
Рероллы: {player.rerolls}

Если хочешь увидеть инвентарь, нажми на 📦, или введи `{config.Bot.prefix}покажи инвентарь`
Если хочешь увидеть навыки и особенности, нажми на 🔸, или введи `{config.Bot.prefix}покажи навыки`

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

    elif message.content.lower().startswith(config.Bot.prefix + 'покажи'):
        map = mapparser.Map(config.Map.path)
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
            elif args[1] in ["инвентарь", "шмотки", "рюкзак"]:
                await send_inventory(message, player)
            else:
                await message.channel.send(f'Неправильное использование команды:\n{command_help.get_commands("покажи")}')
        else:
            await message.channel.send(f'Неправильное использование команды:\n{command_help.get_commands("покажи")}')
    
    elif message.content.lower().startswith(config.Bot.prefix + 'где я'):
        map = mapparser.Map(config.Map.path)
        player = map.get_player(message.author.display_name, message.author.id)

        if player == mapparser.MapObjectError.NOT_FOUND:
            await message.channel.send("Ты не существуешь.")
            return
        elif player == mapparser.MapObjectError.WRONG_ID:
            await message.channel.send("Ты меня обмануть пытаешься?")
            return

        resp = '```ansi\n'+map.construct_ascii_repr(player)+'\n```\n'+map.list_doors_string(player)
        await message.reply(resp)

    elif message.content.lower().startswith(config.Bot.prefix + "группа"):
        groupRole: discord.Role = None
        for role in message.author.roles:
            if role.name.startswith("группа"):
                groupRole = role
                break
        else:
            await message.channel.send("Ты не находишься в группе.")
            return

        map = mapparser.Map(config.Map.path)
        groupMembers = list(groupRole.members)
        msg = "```ansi\n"
        
        for member in groupMembers:
            player = map.get_player(member.display_name, member.id)
            msg += f"{member.display_name}: <[31m{player.HP}/{player.maxHP}[0m> "
            if player.maxMP > 0:
                msg += f"<[34m{player.MP}/{player.maxMP}[0m>"
            msg += "\n"
        
        msg += "\n```"
        await message.channel.send(msg)

    elif message.content.lower().startswith(config.Bot.prefix + 'инвентарь'):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        if len(message.content.split("\n")) < 2:
            if len(message.content.split()) >= 2:
                map = mapparser.Map(config.Map.path)
                inv = map.get_objects_inventory(" ".join(message.content.split()[1::]))
                
                if inv is mapparser.MapObjectError.NOT_FOUND:
                    await message.channel.send("Объекта с таким именем нет на карте.")
                    return

                await send_inventory(message, inv, format=False)
                return

            await message.channel.send("А инвентарь-то где?")
            return

        await send_inventory(message, message.content.split("\n")[1::])

    elif message.content.lower().startswith(config.Bot.prefix + "выбери"):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return
        
        args = message.content.split()
        if len(args) >= 2:
            map = mapparser.Map(config.Map.path)
            if args[1] == "игрока":
                await message.delete()

                candidates = []
                try:
                    levelNeeded: int = int(args[2]) if len(args) >= 3 and not args[2].startswith("<@&") else 0
                    excludeRole: discord.Role = message.role_mentions[0] if message.role_mentions else None

                    for user in message.guild.members:
                        if user.status == discord.Status.online and \
                        excludeRole not in user.roles:
                            if not isinstance(player := map.get_player(user.display_name, user.id), 
                                            mapparser.MapObjectError):
                                if (levelNeeded == 0) or (levelNeeded == player.level):
                                    candidates.append(player)
                except ValueError:
                    ...
                if candidates:
                    await message.channel.send(random.choice(candidates))
                else:
                    await message.channel.send("По таким критериям я никого не нашёл.")
            else:
                await message.channel.send("Выбрать что?")
        else:
            await message.channel.send("Выбрать что?")

    elif message.content.lower().startswith(config.Bot.prefix + 'карта'):
        map = mapparser.Map(config.Map.path)
        player = map.get_player(message.author.display_name, message.author.id)

        if player == mapparser.MapObjectError.NOT_FOUND:
            await message.channel.send("Ты не существуешь.")
            return
        elif player == mapparser.MapObjectError.WRONG_ID:
            await message.channel.send("Ты меня обмануть пытаешься?")
            return
        if 'карта' not in command_help.list_inventory_commands(player):
            await message.channel.send("У тебя нет карты.")
            return

        resp = '```\n'+map.construct_ascii_map(player)+'```'
        await message.reply(resp)

if __name__ == '__main__':
    client.run(config.Bot.token)
