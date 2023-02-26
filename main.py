#!/usr/bin/env python3
import os
import sys
from typing import Tuple, Union
import shlex
import random
import platform
import discord
from discord.ui import Button
from buttons import WhoamiCommandView, VoteCommandView
from config import Config, ReactionTrigger
from player import Player
import command_help
import mapparser
import casino
import dialog_manager as dialog


config_name = "botconfig.cfg"
scriptDir = os.path.dirname(os.path.realpath(__file__))
configPath = os.path.join(scriptDir, config_name)
fallbackConfigPath = os.path.join(scriptDir, "config_example.cfg")
config = Config(configPath if os.path.exists(configPath) else fallbackConfigPath)
intents = discord.Intents.all()
client = discord.Client(intents=intents)

blackjack = casino.Blackjack()


async def get_map_and_player(message: discord.Message) -> (
        Union[Tuple[mapparser.Map, Player], None]
    ):
    try:
        gameMap = mapparser.Map(config.MapConfig.path)
        player = gameMap.get_player(message.author.display_name, message.author.id)

        return (gameMap, player)
    except mapparser.MapObjectNotFoundException:
        await message.channel.send("Ты не существуешь.")
        return None
    except mapparser.MapObjectWrongIDException:
        await message.channel.send("Ты меня обмануть пытаешься?")
        return None

async def get_reaction_trigger_data(payload: discord.RawReactionActionEvent) -> (
        Union[Tuple[discord.Role, discord.Member, str], None]
    ):
    trigger: Union[ReactionTrigger, None] = \
        config.BotConfig.search_reaction_trigger(message_id=payload.message_id)
    if trigger is not None:
        emoji = payload.emoji.id or payload.emoji.name
        emoji = str(emoji)
        if emoji in trigger.emojis:
            reaction_role, reaction_message = trigger.get_data_by_emoji(emoji)

            guild = client.get_guild(payload.guild_id)
            role = guild.get_role(reaction_role)
            member = guild.get_member(payload.user_id)
            return (role, member, reaction_message)
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
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    search_result = await get_reaction_trigger_data(payload)
    if search_result is None:
        return
    role, member, reaction_message = search_result
    await member.add_roles(role)
    await member.send(reaction_message.split("/")[0])

@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    search_result = await get_reaction_trigger_data(payload)
    if search_result is None:
        return
    role, member, reaction_message = search_result
    await member.remove_roles(role)
    await member.send(reaction_message.split("/")[1])

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    #region [user commands]

    if message.content.lower().startswith(config.BotConfig.prefix + "помоги"):
        game_map = mapparser.Map(config.MapConfig.path)
        player = game_map.get_player(message.author.display_name, message.author.id)

        splitted_message = message.content.split()
        if len(splitted_message) == 1:
            await message.channel.send(command_help.get_commands(player=player))
        elif len(splitted_message) >= 2:
            if splitted_message[1] == "мне":
                await message.channel.send("Сам справишься.")
            elif splitted_message[1] == "админу":
                if str(message.author.id) in config.BotConfig.admins:
                    await message.channel.send(
                        command_help.get_admin_command(
                            splitted_message[2] if len(splitted_message) >= 3 else None
                        )
                    )
                else:
                    await message.channel.send("Ты кто вообще такой?")
            else:
                await message.channel.send(command_help.get_commands(" ".join(splitted_message[1::]), player))

    elif message.content.lower().startswith(
        (config.BotConfig.prefix + 'кто я', config.BotConfig.prefix + 'я кто')
        ):
        data = await get_map_and_player(message)
        if data is not None:
            game_map, player = data
            view = WhoamiCommandView(game_map, player, message.author, False)
            view.message = await message.reply(
                dialog.get_player_info_string(game_map, player),
                view=view)

    elif message.content.lower().startswith(config.BotConfig.prefix + 'покажи'):
        data = await get_map_and_player(message)
        if data is not None:
            _, player = data
            args = message.content.lower().split()
            if len(args) == 2:
                if args[1] in ["скиллы", "способности", "особенности",
                               "навыки", "спеллы", "абилки"]:
                    await dialog.send_abilities(message, player)
                elif args[1] in ["инвентарь", "шмотки", "рюкзак"]:
                    await dialog.send_player_inventory(message, player)
                elif args[1] in ["колоду"]:
                    if str(message.author.id) not in config.BotConfig.admins:
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

    elif message.content.lower().startswith(config.BotConfig.prefix + 'где я'):
        data = await get_map_and_player(message)
        if data is not None:
            game_map, player = data
            view = WhoamiCommandView(game_map, player, message.author, True)
            view.message = await message.reply(
                dialog.get_player_position_string(game_map, player),
                view=view)

    elif message.content.lower().startswith(config.BotConfig.prefix + "группа"):
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

        game_map = mapparser.Map(config.MapConfig.path)
        groupMembers = list(groupRole.members) if groupRole is not None else [message.author]
        msg = "```ansi\n"

        for member in groupMembers:
            player = game_map.get_player(member.display_name, member.id)
            msg += f"{member.display_name}: <[31m{player.HP}/{player.maxHP}[0m> "
            if player.maxMP > 0:
                msg += f"<[34m{player.MP}/{player.maxMP}[0m>"
            msg += "\n"

        msg += "\n```"
        await message.channel.send(msg)

    #endregion

    #region [admin commands]

    elif message.content.lower().startswith(config.BotConfig.prefix + 'инвентарь'):
        if str(message.author.id) not in config.BotConfig.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        if len(message.content.split("\n")) < 2:
            if len(message.content.split()) >= 2:
                game_map = mapparser.Map(config.MapConfig.path)
                try:
                    inv = game_map.get_objects_inventory(" ".join(message.content.split()[1::]))
                    await dialog.send_formatted_inventory(message, inv, format_inventory=False)
                except mapparser.MapObjectNotFoundException:
                    await message.channel.send("Объекта с таким именем нет на карте.")
                    return
            else:
                await message.channel.send("А инвентарь-то где?")
        else:
            await dialog.send_formatted_inventory(message, message.content.split("\n")[1::])

    elif message.content.lower().startswith(config.BotConfig.prefix + "перезапусти"):
        if str(message.author.id) not in config.BotConfig.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        await message.channel.send("R.E.S.T.A.R.T protocol engaged...")

        with open(".rst", "w") as f:
            f.write(str(message.channel.id))

        if platform.system() == "Linux":
            os.execv(__file__, sys.argv)
        elif platform.system() == "Windows":
            os.execv(sys.executable, ["python"] + sys.argv)

    elif message.content.lower().startswith(config.BotConfig.prefix + "выбери"):
        if str(message.author.id) not in config.BotConfig.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        args = message.content.split()
        if len(args) >= 2:
            game_map = mapparser.Map(config.MapConfig.path)
            if args[1] == "игрока":
                await message.delete()

                candidates = []
                try:
                    levelNeeded: int = int(args[2]) if len(args) >= 3 and not args[2].startswith("<@&") else 0
                    excludeRole: discord.Role = message.role_mentions[0] if message.role_mentions else None

                    for user in message.guild.members:
                        if user.status == discord.Status.online and \
                        excludeRole not in user.roles:
                            try:
                                player = game_map.get_player(user.display_name, user.id)
                                if (levelNeeded == 0) or (levelNeeded == player.level):
                                    candidates.append(player)
                            except mapparser.MapObjectNotFoundException:
                                continue
                except ValueError:
                    ...
                if candidates:
                    await message.channel.send(random.choice(candidates))
                else:
                    await message.channel.send("По таким критериям я никого не нашёл.")
            elif args[1] == "карту":
                card = blackjack.draw_card()
                await message.channel.send(f"Ты вытянул {card}")
            elif args[1] == "уведомление":
                await dialog.add_reaction_message(message, config, True)
            else:
                await message.channel.send("Выбрать что?")
        else:
            await message.channel.send("Выбрать что?")

    elif message.content.lower().startswith(config.BotConfig.prefix + "сбрось"):
        if str(message.author.id) not in config.BotConfig.admins:
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

    elif message.content.lower().startswith(config.BotConfig.prefix + "создай"):
        if str(message.author.id) not in config.BotConfig.admins:
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
            elif args[1] == "уведомление":
                await dialog.add_reaction_message(message, config, False)
            else:
                await message.channel.send("Создать что?")
        else:
            await message.channel.send("Создать что?")

    elif message.content.lower().startswith(config.BotConfig.prefix + "кто"):
        if str(message.author.id) not in config.BotConfig.admins:
            await message.channel.send(
                f"Ты можешь осматривать только себя (`{config.BotConfig.prefix}кто я`)."
            )
            return

        mentions = message.mentions
        if not mentions:
            await message.channel.send(
                "Необходимо упомянуть игрока, которого ты хочешь осмотреть."
            )
            return
        game_map = mapparser.Map(config.MapConfig.path)
        user = mentions[0]
        try:
            player = game_map.get_player(user.display_name, user.id)
            await message.channel.send(dialog.get_player_info_string(game_map, player))
            await dialog.send_player_inventory(message, player)
            await dialog.send_abilities(message, player)
        except mapparser.MapObjectNotFoundException:
            await message.channel.send("Такой игрок не найден.")
            return

    elif message.content.lower().startswith(config.BotConfig.prefix + "удали"):
        if str(message.author.id) not in config.BotConfig.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        args = message.content.split()
        if len(args) >= 2:
            if args[1] == "уведомление":
                await message.delete()
                if not message.reference:
                    await message.channel.send("Ты должен ответить на сообщение, к которому привязаны уведомления.")
                    return

                trigger: ReactionTrigger = config.BotConfig.search_reaction_trigger(message_id=message.reference.message_id)
                if trigger is None:
                    await message.channel.send("К этому сообщению не привязаны уведомления.")
                    return

                config.BotConfig.remove_reaction_trigger(trigger=trigger)
                config.BotConfig.write_reaction_triggers_file()
                msg = await message.channel.fetch_message(message.reference.message_id)
                await msg.clear_reactions()
            else:
                await message.channel.send("Удалить что?")
        else:
            await message.channel.send("Удалить что?")

    elif message.content.lower().startswith(config.BotConfig.prefix + "спроси"):
        if str(message.author.id) not in config.BotConfig.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        args = message.content.split()

        if len(args) >= 2:
            if args[1] == "всех" or message.role_mentions:
                await message.delete()

                voting_users = []
                if message.role_mentions:
                    voting_users = message.role_mentions[0].members

                command_line = message.content.split("\n")[0]
                command_args = shlex.split(command_line)
                timeout = 300
                anonymous = False
                can_revote = False
                force_stop_by_admin = True
                force_stop_by_variant = True

                if any(i for i in command_args if i == "-время"):
                    try:
                        timeout = int(command_args[command_args.index("-время")+1])
                    except Exception:
                        await message.channel.send("Опция `-время` введена неверно.")
                if any(i for i in command_args if i == "-анон"):
                    anonymous = True
                if any(i for i in command_args if i == "-переголосование"):
                    can_revote = True
                if any(i for i in command_args if i == "-админ"):
                    force_stop_by_admin = False
                if any(i for i in command_args if i == "-вето"):
                    force_stop_by_variant = False

                if not '"' in message.content.split("\n")[0]:
                    await message.channel.send("Ты должен ввести название голосования.")
                    return

                title = message.content.split('"')[1]

                view = VoteCommandView(
                    title=title,
                    timeout=timeout,
                    can_revote=can_revote,
                    anonymous=anonymous,
                    force_stop=force_stop_by_admin,
                    admin_id=message.author.id,
                    voting_users=voting_users
                )

                if len(message.content.split("\n")[1::]) > 1:
                    for label in message.content.split("\n")[1::]:
                        if label.startswith("!") and force_stop_by_variant:
                            view.add_item(Button(label=label[1:], style=discord.ButtonStyle.red), True)
                        else:
                            view.add_item(Button(label=label, style=discord.ButtonStyle.primary))
                else:
                    view.add_item(Button(label="За", style=discord.ButtonStyle.primary))
                    view.add_item(
                        Button(
                            label="Против",
                            style=discord.ButtonStyle.red if force_stop_by_variant else discord.ButtonStyle.primary),
                        force_stop_by_variant)

                view.message = await message.channel.send(content=view.get_voting_message_str(), view=view)
                await view.message.pin()
        else:
            await message.channel.send("Спросить кого?")

    elif message.content.lower().startswith(
        (config.BotConfig.prefix + "экип", config.BotConfig.prefix + "экипировка")
        ):
        if str(message.author.id) not in config.BotConfig.admins:
            await message.channel.send("Ты как сюда попал, шизанутый?")
            return

        if len(message.content.split()) >= 2:
            game_map = mapparser.Map(config.MapConfig.path)
            try:
                objectname = " ".join(message.content.split()[1::])
                inv = game_map.get_objects_inventory(objectname, True)
                formatted_inv = dialog.get_formatted_inventory(inv, False)
                await message.delete()
                await message.channel.send(f"Экипировка {objectname}:\n{formatted_inv}")

            except mapparser.MapObjectNotFoundException:
                await message.channel.send("Объекта с таким именем нет на карте.")
                return
        else:
            await message.channel.send("Введи название объекта.")

    #endregion

    #region [item-related commands]

    elif message.content.lower().startswith(config.BotConfig.prefix + 'карта'):
        data = await get_map_and_player(message)
        if data is not None:
            game_map, player = data
            invItems = command_help.list_inventory_commands(player)
            if 'карта' not in invItems:
                await message.channel.send("У тебя нет карты.")
                return
            floorString = game_map.get_floor_string(player)
            asciiMap = game_map.construct_ascii_map(player, invItems['карта'])
            resp = f'```ansi\n{floorString}\n\n{asciiMap}```'
            await message.reply(resp)

    #endregion

if __name__ == '__main__':
    client.run(config.BotConfig.token)
