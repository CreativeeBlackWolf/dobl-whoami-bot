import configparser
import player as pl
import re
from main import prefix

commands = {
    "кто я": f"Вывести своего персонажа // `{prefix}кто я`",
    "покажи": f"Показать инвентарь или особенности/навыки персонажа // `{prefix}покажи [инвентарь|навыки]`",
    "помоги": f"Вывести это сообщение или помощь для конкретной команды // `{prefix}помоги <команда>`",
    "группа": f"Показать состояние группы // `{prefix}группа`"
}

aliases = {
    "кто я": f"`{prefix}я кто`",
    "покажи": f"""Показать инвентарь: `{prefix}покажи [шмот|инвентарь|рюкзак]`
Показать навыки/особенности: `{prefix}покажи [скиллы|способности|особенности|навыки|спеллы|абилки]`
"""
}

invCommands = {
    "карта": f"Показать карту // `{prefix}карта`",
}

def get_commands(command: str = None, player: pl.Player = None) -> str:
    if command is not None:
        com = commands.get(command)
        if com is None:
            return "Такой команды нет."
        return com + "\nАльтернативные написания:\n" + aliases.get(command, "`Нет`")
    s = ""
    for _, v in commands.items():
        s += v + "\n"
    if not isinstance(player, pl.Player):
        return s
    invCmds = list_inventory_commands(player)
    if len(invCmds) > 0:
        for i in invCmds:
            s += invCommands.get(i) + "\n"
    return s

def list_inventory_commands(player: pl.Player) -> list:
    """
    List all commands added by inventory items

    :param player: the player in question
    :return: list of commands
    """
    commands = []
    for item in player.inventory:
        matches = re.findall("<"+re.escape(prefix)+".+>", item)
        for match in matches:
            commands.append(match[2:-1])
    return commands

def get_alias(command: str) -> str:
    return aliases.get(command, "Такой команды нет.")
