from typing import Union
import xml.etree.ElementTree as etree
import datetime
import os
import player


class Map:
    def __init__(self, filepath):
        # read the file
        tree = etree.parse(filepath)
        self.root = tree.getroot()
        time = os.path.getmtime(filepath)
        self.map_datetime = datetime.datetime.fromtimestamp(time).strftime('%H:%M:%S %d/%m/%Y')

    def search_player(self, playername: str) -> Union[etree.Element, None]:
        """
        Search for a player in the map.

        :param playername: the name of the player to search for
        :return: the player's root element or None if no match found
        """
        for objectgroup in self.root.findall("objectgroup"):
            if objectgroup.attrib["name"] in ["нижний", "средний", "верхний"]:
                for object in objectgroup.findall("object"):
                    if object.attrib["name"] == playername:
                        return object

    def get_player(self, playername: str) -> Union[player.Player, None]:
        """
        Get serialized Player object

        :param playername: the name of the player to search for
        :return: Player object or None if player not found
        """
        pl = self.search_player(playername)
        if not pl:
            return None
        name = pl.attrib["name"]
        position = [pl.attrib["x"], pl.attrib["y"]]
        props = {prop.attrib["name"]: prop.attrib.get("value") or prop.text 
                    for prop in pl.find("properties").findall("property")}
        inventory = props["Инвентарь"].split("\n")
        hp = props["Очки Здоровья"]
        mp = props["Очки Маны"]
        sp = props["Очки Души"]
        rerolls = int(props["Рероллы"])
        active_abilities = props["Навыки"].split("\n")
        passive_abilities = props["Особенности"].split("\n")
        level = props["Уровень"]
        frags = props["Фраги"]
        return player.Player(position, name, inventory, hp, mp, sp, 
        level, frags, active_abilities, passive_abilities, rerolls)

