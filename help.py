commands = {
    "кто я": "Вывести своего персонажа // ~кто я",
    "покажи": "Показать инвентарь или особенности/навыки персонажа // ~покажи [инвентарь/навыки]",
    "помоги": "Вывести это сообщение // ~помоги"
}

def get_commands(command: str = None) -> str:
    if command is not None:
        return commands.get(command, "Такой команды нет.")
    s = ""
    for _, v in commands.items():
        s += v + "\n"
    return s