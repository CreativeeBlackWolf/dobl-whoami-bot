#!/usr/bin/env python3
import os
import sys
import random
import platform
from typing import Tuple, Union
import discord
from dialog_manager import (send_abilities,
                            send_player_inventory,
                            send_formatted_inventory,
                            get_player_info_string,
                            get_inventory_string,
                            get_abilities_string)
from buttons import WhoamiCommandView
from config import Config
import mapparser
import command_help
from player import Player
import casino


config = Config("botconfig.cfg")
intents = discord.Intents.all()
client = discord.Client(intents=intents)

blackjack = casino.Blackjack()


async def get_map_and_player(message: discord.Message) -> (
        Union[Tuple[mapparser.Map, Player], None]
    ):
    try:
        gameMap = mapparser.Map(config.Map.path)
        player = gameMap.get_player(message.author.display_name, message.author.id)

        return (gameMap, player)
    except mapparser.MapObjectNotFoundException:
        await message.channel.send("Ты не существуешь.")
        return None
    except mapparser.MapObjectWrongIDException:
        await message.channel.send("Ты меня обмануть пытаешься?")
        return None

@client.event
async def on_ready():
    if os.path.exists(".rst"):
        with open(".rst", "r") as f:
            channel: discord.channel.TextChannel = client.get_channel(int(f.read()))
        await channel.send("Перезапуск завершён.")
        os.remove(".rst")
    print(f'We have logged in as {client.user}')
    await client.change_presence(activity=discord.Game(name="напиши .помоги"))


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    #region [user commands]

    if message.content.lower().startswith(config.Bot.prefix + "помоги"):
        gameMap = mapparser.Map(config.Map.path)
        player = gameMap.get_player(message.author.display_name, message.author.id)

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
        data = await get_map_and_player(message)
        if data is not None:
            gameMap, player = data
            view = WhoamiCommandView(gameMap, player, message.author)
            view.message = await message.reply(get_player_info_string(gameMap, player), view=view)

    elif message.content.lower().startswith(config.Bot.prefix + 'покажи'):
        data = await get_map_and_player(message)
        if data is not None:
            _, player = data
            args = message.content.lower().split()
            if len(args) == 2:
                if args[1] in ["скиллы", "способности", "особенности", 
                               "навыки", "спеллы", "абилки"]:
                    await send_abilities(message, player)
                elif args[1] in ["инвентарь", "шмотки", "рюкзак"]:
                    await send_player_inventory(message, player)
                elif args[1] in ["колоду"]:
                    if str(message.author.id) not in config.Bot.admins:
                        await message.channel.send("Размечтался.")
                        return
                    await message.author.send(
                        "`" + ", ".join([i.replace("\\", "") for i in blackjack.deck]) + "`"
                    )
                else:
                    await message.channel.send(
                        f'Неправильное использование команды:\n{command_help.get_commands("покажи")}'
                    )
            else:
                await message.channel.send(
                    f'Неправильное использование команды:\n{command_help.get_commands("покажи")}'
                )

    elif message.content.lower().startswith(config.Bot.prefix + 'где я'):
        data = await get_map_and_player(message)
        if data is not None:
            gameMap, player = data
            resp = f"""```ansi
{gameMap.construct_ascii_room(player)}

{gameMap.list_doors_string(player)}
```"""
            await message.reply(resp)

    elif message.content.lower().startswith(config.Bot.prefix + "группа"):
        ingame: bool = False
        groupRole: discord.Role = None
        for role in message.author.roles:
            if role.name.startswith("в игре"):
                ingame = True
            elif role.name.startswith("группа"):
                groupRole = role
                break

        if not ingame:
            await message.channel.send("Ты не в игре.")
            return

        gameMap = mapparser.Map(config.Map.path)
        groupMembers = list(groupRole.members) if groupRole is not None else [message.author]
        msg = "```ansi\n"

        for member in groupMembers:
            player = gameMap.get_player(member.display_name, member.id)
            msg += f"{member.display_name}: <[31m{player.HP}/{player.maxHP}[0m> "
            if player.maxMP > 0:
                msg += f"<[34m{player.MP}/{player.maxMP}[0m>"
            msg += "\n"

        msg += "\n```"
        await message.channel.send(msg)

    #endregion

    #region [admin commands]

    elif message.content.lower().startswith(config.Bot.prefix + 'инвентарь'):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        if len(message.content.split("\n")) < 2:
            if len(message.content.split()) >= 2:
                gameMap = mapparser.Map(config.Map.path)
                try:
                    inv = gameMap.get_objects_inventory(" ".join(message.content.split()[1::]))

                except mapparser.MapObjectNotFoundException:
                    await message.channel.send("Объекта с таким именем нет на карте.")
                    return

                await send_formatted_inventory(message, inv, formatInventory=False)
                return

            await message.channel.send("А инвентарь-то где?")
            return

        await send_formatted_inventory(message, message.content.split("\n")[1::])

    elif message.content.lower().startswith(config.Bot.prefix + "перезапусти"):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        await message.channel.send("R.E.S.T.A.R.T protocol engaged...")

        with open(".rst", "w") as f:
            f.write(str(message.channel.id))

        if platform.system() == "Linux":
            os.execv(__file__, sys.argv)
        elif platform.system() == "Windows":
            os.execv(sys.executable, ["python"] + sys.argv)

    elif message.content.lower().startswith(config.Bot.prefix + "выбери"):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        args = message.content.split()
        if len(args) >= 2:
            gameMap = mapparser.Map(config.Map.path)
            if args[1] == "игрока":
                await message.delete()

                candidates = []
                try:
                    levelNeeded: int = int(args[2]) if len(args) >= 3 and not args[2].startswith("<@&") else 0
                    excludeRole: discord.Role = message.role_mentions[0] if message.role_mentions else None

                    for user in message.guild.members:
                        if user.status == discord.Status.online and \
                        excludeRole not in user.roles:
                            if not isinstance(player := gameMap.get_player(user.display_name, user.id),
                                            mapparser.MapObjectError):
                                if (levelNeeded == 0) or (levelNeeded == player.level):
                                    candidates.append(player)
                except ValueError:
                    ...
                if candidates:
                    await message.channel.send(random.choice(candidates))
                else:
                    await message.channel.send("По таким критериям я никого не нашёл.")
            elif args[1] == "карту":
                card = blackjack.draw_card()
                await message.channel.send(f"Ты вытянул {card}")
            else:
                await message.channel.send("Выбрать что?")
        else:
            await message.channel.send("Выбрать что?")

    elif message.content.lower().startswith(config.Bot.prefix + "сбрось"):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        args = message.content.split()
        if len(args) >= 2:
            if args[1] == "колоду":
                blackjack.shuffle_deck()
                await message.channel.send("Колода перемешана.")
            else:
                await message.channel.send("Сбросить что?")
        else:
            await message.channel.send("Сбросить что?")

    elif message.content.lower().startswith(config.Bot.prefix + "создай"):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        args = message.content.split()

        if len(args) >= 2:
            if args[1] == "группу":
                await message.delete()

                appendRole: discord.Role = message.role_mentions[0] if message.role_mentions else None
                inGameRole: discord.Role = [role for role in message.guild.roles if role.name == "в игре"][0]
                if appendRole is None:
                    await message.channel.send("Упомяни роль, она всё равно удалится.")
                    return

                appenders: list[Union[discord.User, discord.Member]] = message.mentions
                if not appenders:
                    await message.channel.send("Упомяни пользователей, которым присвоить роль. " + \
                                               "Упоминания всё равно удалятся")
                    return

                for user in appenders:
                    await user.add_roles(appendRole, inGameRole)

                await message.channel.send(f"Группа <@&{appendRole.id}> сформирована.")
            else:
                await message.channel.send("Создать что?")
        else:
            await message.channel.send("Создать что?")

    elif message.content.lower().startswith(config.Bot.prefix + "кто"):
        if str(message.author.id) not in config.Bot.admins:
            await message.channel.send(
                f"Ты можешь осматривать только себя ({config.Bot.prefix}кто я)."
            )
            return

        mentions = message.mentions
        if not mentions:
            await message.channel.send(
                "Необходимо упомянуть игрока, которого ты хочешь осмотреть."
            )
            return
        gameMap = mapparser.Map(config.Map.path)
        user = mentions[0]
        try:
            player = gameMap.get_player(user.display_name, user.id)
            await message.channel.send(get_player_info_string(gameMap, player))
            await message.channel.send(get_inventory_string(player))
            await message.channel.send(get_abilities_string(player))
        except mapparser.MapObjectNotFoundException:
            await message.channel.send("Такой игрок не найден.")
            return

    #endregion

    #region [item-related commands]

    elif message.content.lower().startswith(config.Bot.prefix + 'карта'):
        data = await get_map_and_player(message)
        if data is not None:
            gameMap, player = data
            if 'карта' not in command_help.list_inventory_commands(player):
                await message.channel.send("У тебя нет карты.")
                return

            resp = '```\n'+gameMap.construct_ascii_map(player)+'```'
            await message.reply(resp)

    #endregion

if __name__ == '__main__':
    client.run(config.Bot.token)
