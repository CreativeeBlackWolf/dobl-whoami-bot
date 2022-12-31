import discord
from discord import app_commands
from discord.ui import Button, View
from discord.ext import commands
from typing import Optional, Union
from config import Config
import requests
import context_dialog_manager as dialog
import command_help
import mapparser
import buttons


class Client(commands.Bot):
    def __init__(self, configpath: str="botconfig.cfg"):
        self.config = Config(configpath)
        super().__init__(command_prefix=self.config.Bot.prefix, intents=discord.Intents.all())

    async def setup_hook(self) -> None:
        # still dk how does this actually works
        self.tree.copy_global_to(guild = discord.Object(id=self.config.Bot.guild_id))
        await self.tree.sync(guild = discord.Object(id=self.config.Bot.guild_id))
        print(f"Synced slash commands for {self.user}")

client = Client()

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="напиши /помоги"))
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


@client.tree.command(name="пинг", description="1, 2, 3, проверка связи...")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("понг блядь.")


@client.hybrid_command(name="ктоя", with_app_command=True, description="Вывести своего персонажа")
async def whoami(ctx: Union[commands.Context, discord.Interaction]):
    map = mapparser.Map(client.config.Map.path)
    player = map.get_player(ctx.author.display_name, ctx.author.id)

    if player == mapparser.MapObjectError.NOT_FOUND:
        await ctx.reply("Ты не существуешь.")
        return
    elif player == mapparser.MapObjectError.WRONG_ID:
        await ctx.reply("Ты меня обмануть пытаешься?")
        return

    view = buttons.WhoamiCommandView(map, player, ctx)

    view.message = await ctx.reply(
        dialog.get_player_info(map, player), 
        view=view, 
        ephemeral=True if player.group == "Скрыт" else False
    )


@client.hybrid_command(name="помоги", with_app_command=True, description="Помощь по командам")
@app_commands.describe(command="Команда, для которой требуется получить помощь")
async def help(ctx: commands.Context, command: Optional[str] = None):
    if command == "мне":
        await ctx.reply("Сам справишься", ephemeral=True)
        return
    player = mapparser.Map(client.config.Map.path).get_player(ctx.author.display_name, ctx.author.id)
    await ctx.reply(command_help.get_commands(command, player), ephemeral=True)


@client.hybrid_command(name="покажи", with_app_command=True, description="Показать инвентарь или навыки персонажа")
@app_commands.describe(showtype="навыки или инвентарь")
async def show_player(ctx: Union[commands.Context, discord.Interaction], showtype: str):
    player = mapparser.Map(client.config.Map.path).get_player(ctx.author.display_name, ctx.author.id)
    
    if player == mapparser.MapObjectError.NOT_FOUND:
        await ctx.reply("Ты не существуешь.")
        return
    elif player == mapparser.MapObjectError.WRONG_ID:
        await ctx.reply("Ты меня обмануть пытаешься?")
        return
    
    if showtype in ["инвентарь", "рюкзак"]:
        await ctx.reply(dialog.get_inventory_string(player))
    elif showtype in ["скиллы", "способности", "особенности", "навыки", "спеллы", "абилки"]:
        await ctx.reply(dialog.get_abilities_string(player))
    else:
        await ctx.reply(f"Неправильное использование команды. Введи `/помоги покажи`.")

@client.hybrid_command(name="группа", description="Показать состояние группы", with_app_command=True)
async def team_stats(ctx: commands.Context):
    groupRole: discord.Role = None
    for role in ctx.author.roles:
        if role.name.startswith("группа"):
            groupRole = role
            break
    else:
        await ctx.reply("Ты не находишься в группе")
        return

    map = mapparser.Map(client.config.Map.path)
    groupMembers = list(groupRole.members)
    msg = "```ansi\n"
    
    for member in groupMembers:
        player = map.get_player(member.display_name, member.id)
        msg += f"{member.display_name}: <[31m{player.HP}/{player.maxHP}[0m> "
        if player.maxMP > 0:
            msg += f"<[34m{player.MP}/{player.maxMP}[0m>"
        msg += "\n"
    
    msg += "\n```"
    await ctx.reply(msg)

if __name__ == "__main__":
    client.run(client.config.Bot.token)
    try:
        data = requests.get("https://discord.com/api/v10/users/@me", headers={
            "Authorization": f"Bot {client.config.Bot.token}"
        }).json()
    except requests.exceptions.RequestException as e:
        if e.__class__ == requests.exceptions.ConnectionError:
            exit(f"ConnectionError: Discord is commonly blocked on public networks, please make sure discord.com is reachable!")

        elif e.__class__ == requests.exceptions.Timeout:
            exit(f"Timeout: Connection to Discord's API has timed out (possibly being rate limited?)")

        exit(f"Unknown error has occurred! Additional info:\n{e}")
