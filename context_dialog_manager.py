from multipledispatch import dispatch
import player
import mapparser


def get_player_info(map: mapparser.Map, player: player.Player) -> str:
    return f'''```
ОЗ: {player.format_HP()}
ОМ: {player.format_MP()}
ОД: {player.SP}
УР: {player.level}
ФРА: {player.frags}
Рероллы: {player.rerolls}

Персонаж актуален на момент времени: {map.map_datetime}.
Учитывай, что данные за время могли измениться.
```'''

def get_inventory_string(player: player.Player) -> str:
    inv = "\n".join(player.inventory)
    return f'''```ansi
Инвентарь:
{inv}
```'''

def get_abilities_string(player: player.Player) -> str:
    active = "\n".join(player.active_abilities)
    passive = "\n".join(player.passive_abilities)
    return f'''```ansi
Навыки:
{active}

Особенности:
{passive}
```'''
