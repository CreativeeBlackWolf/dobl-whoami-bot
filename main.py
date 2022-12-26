import configparser
import discord
import mapparser
import help
import asyncio


config = configparser.ConfigParser()
config.read('botconfig.cfg')
intents = discord.Intents.default()
intents.message_content = True


client = discord.Client(intents=intents)



async def send_inventory(message, player):
    inv = "\n".join(player.inventory)
    await message.channel.send(f'''```
Инвентарь:
{inv}
```''')

async def send_abilities(message, player):
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

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    map = mapparser.Map(config["map"]["path"])
    playername = message.author.display_name

    if message.content.lower().startswith("~помоги"):
        await message.channel.send(help.get_commands())

    if message.content.lower().startswith('~кто я'):
        player = map.get_player(playername)

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

Если хочешь увидеть инвентарь, нажми на 📦, или введи `~покажи инвентарь`
Если хочешь увидеть навыки и особенности, нажми на 🔸, или введи `~покажи навыки`

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
            await msg.add_reaction("🔸", client.user)
        else:
            if str(reaction.emoji) == "📦":
                await send_inventory(message, player)
            elif str(reaction.emoji) == "🔸":
                await send_abilities(message, player)

    if message.content.lower().startswith('~покажи'):
        player = map.get_player(playername)

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
    
    if message.content.lower().startswith('~где я'):
        await message.channel.send('здесь.')


if __name__ == '__main__':
    bot_token = config['bot']['token']
    client.run(bot_token)
