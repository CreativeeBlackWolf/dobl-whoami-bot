import configparser

config = configparser.ConfigParser()
config.read("botconfig.cfg")
prefix = config.get("bot", "prefix", fallback=".")

commands = {
    "кто я": f"Вывести своего персонажа // `{prefix}кто я`",
    "покажи": f"Показать инвентарь или особенности/навыки персонажа // `{prefix}покажи [инвентарь|навыки]`",
    "помоги": f"Вывести это сообщение или помощь для конкретной команды // `{prefix}помоги <команда>`"
}

aliases = {
    "кто я": f"`{prefix}я кто`",
    "покажи": f"""Показать инвентарь: `{prefix}покажи [шмот|инвентарь]`
Показать навыки/особенности: `{prefix}покажи [скиллы|способности|особенности|навыки|спеллы|абилки]`
"""
}

def get_commands(command: str = None) -> str:
    if command is not None:
        com = commands.get(command)
        if com is None:
            return "Такой команды нет."
        return com + "\nАльтернативные написания:\n" + aliases.get(command, "`Нет`")
    s = ""
    for _, v in commands.items():
        s += v + "\n"
    return s

def get_alias(command: str) -> str:
    return aliases.get(command, "Такой команды нет.")
