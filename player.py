from __future__ import annotations
import re
from colorama import Fore, Style


class Player:
    def __init__(self,
                 position:          list[int], # [x, y]
                 name:              str,
                 inventory:         list[str],
                 HP:                int,
                 maxHP:             float,
                 trueHP:            int,
                 MP:                str,
                 maxMP:             float,
                 trueMP:            int,
                 SP:                float,
                 level:             int,
                 frags:             str, # frags/frags until levelup
                 active_abilities:  list[str],
                 passive_abilities: list[str],
                 rerolls:           int,
                 group:             str,
                 isBlind:           bool,
                 isDead:            bool,
        ):
        self.position = position
        self.name = name
        self.inventory = inventory
        self.HP = HP
        self.maxHP = maxHP
        self.trueHP = trueHP
        self.MP = MP
        self.maxMP = maxMP
        self.trueMP = trueMP
        self.SP = SP
        self.level = level
        self.frags = frags
        self.active_abilities = active_abilities
        self.passive_abilities = passive_abilities
        self.rerolls = rerolls
        self.group = group
        self.isBlind = isBlind
        self.isDead = isDead

    def __str__(self):
        return f"Player: {self.name}"

    def format_HP(self) -> str:
        """
        Formats the player HP for display like `HP/MAXHP (TRUEHP)`
        """
        return f"{self.HP}/{self.maxHP} ({self.trueHP})"

    def format_MP(self) -> str:
        """
        Formats the player MP for display like `MP/MAXMP (TRUEMP)`
        """
        return f"{self.MP}/{self.maxMP} ({self.trueMP})"

    @staticmethod
    def format_inventory_list(inventory: list, show_equipped_only: bool = False) -> list:
        """
        Formats inventory for ANSI display

        :param inventory: list of items
        :param show_equipped_only: show only equipped items
        :return: list of formatted items
        """
        def replacer(match):
            if match.group(1) is not None:
                return "?"
            if match.group(2) is not None:
                return "???,"
            if match.group(3) is not None:
                return "???}"

        formatted_inventory = []

        for item in inventory:
            equipped_item_regex = r"(\d+э)\."
            if show_equipped_only:
                if not re.findall(equipped_item_regex, item):
                    continue
                else:
                    item_name = re.findall(r"э.([\W].+?) [\ |\(|\{|\n]", item)[0][1::]
                    formatted_inventory.append(item_name)
                    continue

            item = item.replace("&lt;", "<")
            item = item.replace("&gt;", ">")
            # replacing hidden properties with `???`
            # (or `?`, if the property partially disclosed)
            item = re.sub(r"\?{3}(\(.*?\))|\?{3}([^,}]*),|\?{3}(.+?)}", replacer, item)
            item = re.sub(r"([^ {]+)\?{3}", r"\1?", item)
            # hiding actual item name
            item = re.sub(r"\(.+?\)", "", item.split("{")[0]) + item[item.find("{")::] if item.find("{") != -1 else item
            item = item.replace("  ", " ")

            # colorize inventory items
            # checking if item equipped
            item = re.sub(equipped_item_regex, rf"{Fore.GREEN}\1{Style.RESET_ALL}.", item)

            # colorizing hidden properties
            item = re.sub(r"\?{3}", f"{Fore.MAGENTA}???{Style.RESET_ALL}", item)

            # colorizing durability (if its less than 25%)
            durability_search_regex = r"(\([0-9]+?\/[0-9]+?\))"
            durability = re.findall(durability_search_regex, item)
            if durability:
                itemDurability, itemMaxDurability = [int(i) for i in durability[0].replace("(", "").replace(")", "").split("/")]
                if itemDurability / itemMaxDurability <= 0.25:
                    item = re.sub(durability_search_regex, Fore.RED + r"\1" + Style.RESET_ALL, item)

            # colorize price
            item = re.sub(r"([0-9]+?ж)", Fore.YELLOW + r"\1" + Style.RESET_ALL, item)

            formatted_inventory.append(item)

        return formatted_inventory \
               or \
               [f"В инвентаре {Fore.RED}нет{Style.RESET_ALL} предметов" if not show_equipped_only
                else f"В инвентаре {Fore.RED}нет{Style.RESET_ALL} экипированных предметов"]
