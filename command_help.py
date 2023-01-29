from __future__ import annotations
import re
import player as pl
from main import config

prefix = config.BotConfig.prefix

commands = {
    "кто я": f"Вывести своего персонажа // `{prefix}кто я`",
    "покажи": f"Показать инвентарь или особенности/навыки персонажа // `{prefix}покажи инвентарь|навыки`",
    "помоги": f"Вывести это сообщение или помощь для конкретной команды // `{prefix}помоги [команда]`",
    "группа": f"Показать состояние группы // `{prefix}группа`"
}

adminCommands = {
    "выбери": f"Выбрать случайного игрока онлайн или карту из колоды // `{prefix}выбери игрока|карту \
[роль|уровень] [роль]`",
    "выбери уведомление": f'Выбрать сообщение, реакция на которое будет давать роль // `{prefix}выбери \
уведомление <эмоция|уведомление_роли> <уведомление_роли|эмоция> \
<сообщение о подписке/сообщение об отписке>`',
    "инвентарь": f"Вывести инвентарь игрока или НПЦ, или отформатировать его // `{prefix}инвентарь \
<имя_объекта|инвентарь для форматирования с новой строки>`",
    "кто": f"Отобразить персонажа для игрока // `{prefix}кто <упоминание>`",
    "создай группу": f"Создать группу из игроков // `{prefix}создай группу <упоминание_группы> \
<упоминания_игроков>`",
    "создай уведомление": f'Создать сообщение, реакция на которое будет давать роль // `{prefix}создай \
уведомление <эмоция|уведомление_роли> <уведомление_роли|эмоция> \
<сообщение о подписке/сообщение об отписке> <текст с новой строки>`',
    "сбрось": f"Сбросить колоду // `{prefix}сбрось колоду`",
    "покажи": f"Показать колоду // `{prefix}покажи колоду`",
    "удали": f"Удалить триггер для сообщения // `{prefix}удали уведомление`"
}

aliases = {
    "кто я": f"`{prefix}я кто`",
    "покажи": f"""Показать инвентарь: `{prefix}покажи шмот|инвентарь|рюкзак`
Показать навыки/особенности: `{prefix}покажи скиллы|способности|особенности|навыки|спеллы|абилки`
"""
}

inventoryCommands = {
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
    invCmds = list_inventory_commands(player).keys()
    if len(invCmds) > 0:
        for i in invCmds:
            s += inventoryCommands.get(i) + "\n"
    return s

def get_admin_command(command: str = None):
    if command is not None:
        com = adminCommands.get(command)
        if com is None:
            return "Такой команды нет."
    s = ""
    for _, v in adminCommands.items():
        s += v + "\n"
    return s

def list_inventory_commands(player: pl.Player) -> dict[str, int]:
    """
    List all commands added by inventory items

    :param player: the player in question
    :return: list of commands
    """
    commands = {}
    for item in player.inventory:
        matches = re.findall(r"<\.(.*?)\+*([0-9]*?)>", item)
        for match in matches:
            if match[0] in commands:
                commands[match[0]] = int(match[1]) \
                                     if match[1] != "" and int(match[1]) > commands[match[0]] \
                                     else commands[match[0]]
            else:
                commands[match[0]] = int(match[1]) if match[1] != "" else 0
    return commands

def get_alias(command: str) -> str:
    return aliases.get(command, "Такой команды нет.")
