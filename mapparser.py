from typing import Union
import xml.etree.ElementTree as etree
import datetime
import player
import os
import re


class Map:
    # name's actually misleading since it's not strictly ASCII
    ASCII_DEFAULT_CHARS = '!"#$%&\'()*+,-./:;<=>?[\\]^_`{|}~0123456789ABCDEFGHIJKLMNOPQRSTUVW'

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
        def replacer(match):
            if match.group(1) is not None:
                return "?"
            if match.group(2) is not None:
                return "???,"
            if match.group(3) is not None:
                return "???}"

        pl = self.search_player(playername)
        if not pl:
            return None
        name = pl.attrib["name"]
        position = [pl.attrib["x"], pl.attrib["y"]]
        props = {prop.attrib["name"]: prop.attrib.get("value") or prop.text
                    for prop in pl.find("properties").findall("property")}
        inventory = [props.get("Инвентарь", "").split("\n")[0]]
        # first item is always the coin(s), so we are skipping it
        for item in props.get("Инвентарь", "").split("\n")[1::]:
            # replacing hidden properties with `???` 
            # (or `?`, if the propertypartially disclosed)
            item = re.sub(r"\?{3}(\(.+?\))|\?{3}(.+?),|\?{3}(.+?)}", replacer, item)
            item = re.sub(r"([^ {]+)\?{3}", r"\1?", item)
            # hiding actual item name
            item = re.sub(r"\(.+?\)", "", item.split("{")[0]) + item[item.find("{")::]
            item = item.replace("  ", " ")
            inventory.append(item)

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

        return sorted(objects, key=lambda x: x[0]+str(x[1])+str(x[2]))

    def construct_ascii_repr(self, player: player.Player) -> str:
        objlist = self.get_same_room_objects(player)
        repr = [["." for i in range(8)] for j in range(8)]
        legend = {}
        usedChars = []
        nextDefaultIndex = 0
        for obj in objlist:
            # check if another object is at same position
            existingChar = repr[obj[2]][obj[1]]
            if existingChar != ".":
                # if so, use the same char
                legend[existingChar].append(obj[0])
                continue
            # find a new char, first candidate is the first letter of the object name
            firstChar = obj[0][0].upper()
            if firstChar in usedChars:
                firstChar = firstChar.lower()
            if firstChar in usedChars:
                firstChar = Map.ASCII_DEFAULT_CHARS[nextDefaultIndex]
                nextDefaultIndex += 1
            assert firstChar not in usedChars, f"Couldn't find a free char for object {obj[0]}"
            if obj[0] == player.name:
                repr[obj[2]][obj[1]] = '[2;34m' + firstChar + '[0m'
            else:
                repr[obj[2]][obj[1]] = firstChar
            usedChars.append(firstChar)
            legend[firstChar] = [obj[0]]
        repr = "\n".join(["".join(row) for row in repr])
        legend = "\n".join([f"{char}: {', '.join(objs)}" for char, objs in legend.items()])
        return f"{repr}\n\n{legend}"
