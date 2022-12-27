import re


class Player:
    def __init__(self, 
                 position:          list, # [x, y]
                 name:              str, 
                 inventory:         list,
                 HP:                str, # HP/MAXHP (TRUE HP)
                 MP:                str, # MP/MAXMP (TRUE MP)
                 SP:                str,
                 level:             str,
                 frags:             str, # frags/frags until levelup
                 active_abilities:  list,
                 passive_abilities: list,
                 rerolls:           str,
                 group:             str
        ):
        self.position = position
        self.name = name
        self.inventory = inventory
        self.HP = HP
        self.MP = MP
        self.SP = SP
        self.level = level
        self.frags = frags
        self.active_abilities = active_abilities
        self.passive_abilities = passive_abilities
        self.rerolls = rerolls
        self.group = group

    def __str__(self):
        return f"Player: {self.name}"

    @staticmethod
    def format_inventory(inventory: list) -> list:
        """
        Formats inventory for ANSI display

        :param inventory: list of items
        :return: list of formatted items
        """
        def replacer(match):
            if match.group(1) is not None:
                return "?"
            if match.group(2) is not None:
                return "???,"
            if match.group(3) is not None:
                return "???}"

        formattedInventory = []

        for item in inventory:
            item = item.replace("&lt;", "<")
            item = item.replace("&gt;", ">")
            # replacing hidden properties with `???` 
            # (or `?`, if the property partially disclosed)
            item = re.sub(r"\?{3}(\(.+?\))|\?{3}(.+?),|\?{3}(.+?)}", replacer, item)
            item = re.sub(r"([^ {]+)\?{3}", r"\1?", item)
            # hiding actual item name
            item = re.sub(r"\(.+?\)", "", item.split("{")[0]) + item[item.find("{")::] if item.find("{") != -1 else item
            item = item.replace("  ", " ")

            # colorize inventory items
            # checking if item equipped
            if "э" in item.split(".")[0]:
                equippedIndex = item.find("э") + 1
                item = "[32m" + item[:equippedIndex] + "[0m" + item[equippedIndex:]
            
            # colorizing hidden properties
            item = re.sub(r"\?{3}", "[35m???[0m", item)

            # colorizing durability (if its less than 25%) 
            durability = re.findall(r"\([0-9]+?\/[0-9]+?\)", item)
            if durability:
                itemDurability, itemMaxDurability = [int(i) for i in durability[0].replace("(", "").replace(")", "").split("/")]
                if itemDurability / itemMaxDurability <= 0.25:
                    durabilityIndex = item.find("(")
                    item = item[:durabilityIndex] + "[31m" + item[durabilityIndex:] + "[0m"
                
            formattedInventory.append(item)

        return formattedInventory
