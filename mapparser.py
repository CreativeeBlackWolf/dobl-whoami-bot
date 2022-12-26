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
        inventory = props.get("Инвентарь", "").split("\n")
        hp = props.get("Очки Здоровья", "100/100 (100)")
        mp = props.get("Очки Маны", "100/100 (100)")
        sp = props.get("Очки Души", "3")
        rerolls = props.get("Рероллы", "2")
        active_abilities = props.get("Навыки", "").split("\n")
        passive_abilities = props.get("Особенности", "").split("\n")
        level = props.get("Уровень", "1")
        frags = props.get("Фраги", "0/4")
        group = props.get("Группа", "")
        return player.Player(position, name, inventory, hp, mp, sp, 
        level, frags, active_abilities, passive_abilities, rerolls, group)

    def get_same_room_objects(self, player: player.Player) -> list:
        """
        Get all objects in the same room as the player
        Hidden objects are not included

        :param player: the player in question
        :return: list of objects
        """
        roomPos = [ int(player.position[0])-int(player.position[0]) % 32,
                    int(player.position[1])-int(player.position[1]) % 32]
        objects = []
        for objectgroup in self.root.findall("objectgroup"):
            if objectgroup.attrib["name"] in ["нижний", "средний", "верхний"]:
                for object in objectgroup.findall("object"):
                    objX, objY = int(object.attrib["x"]), int(object.attrib["y"])
                    if objX-objX % 32 == roomPos[0] and objY-objY % 32 == roomPos[1]:
                        name = object.attrib.get("name", "???")
                        props = {prop.attrib["name"]: prop.attrib.get("value")
                            for prop in object.find("properties").findall("property")}
                        group = props.get("Группа", "")
                        hidden = True if props.get("Скрыт", "false") == "true" else False
                        owner = props.get("Владелец", "")
                        if  (not hidden) or\
                            (owner != "" and owner == player.name) or\
                            (group != "" and group == player.group) or\
                            (name != "???" and name == player.name):
                            objX, objY = objX % 32 // 4, objY % 32 // 4
                            objects.append((object.attrib.get("name", "???"), objX, objY))
                            
        return objects