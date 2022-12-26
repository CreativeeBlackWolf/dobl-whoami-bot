import configparser

config = configparser.ConfigParser()
config.read("botconfig.cfg")
prefix = config["bot"]["prefix"]

commands = {
    "кто я": f"Вывести своего персонажа // {prefix}кто я",
    "покажи": f"Показать инвентарь или особенности/навыки персонажа // {prefix}покажи [инвентарь/навыки]",
    "помоги": f"Вывести это сообщение // {prefix}помоги"
}

def get_commands(command: str = None) -> str:
    if command is not None:
        return commands.get(command, "Такой команды нет.")
    s = ""
    for _, v in commands.items():
        s += v + "\n"
    return s
