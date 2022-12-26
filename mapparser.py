from typing import Union
import xml.etree.ElementTree as etree
import datetime
import player
import os
import re
from enum import Enum

GetPlayerErrors = Enum("GetPlayerErrors", ["NOT_FOUND", "WRONG_ID"])

class Map:
    # name's actually misleading since it's not strictly ASCII
    ASCII_DEFAULT_CHARS = '!"#$%&\'()*+,-./:;<=>?[\\]^_`{|}~0123456789ABCDEFGHIJKLMNOPQRSTUVW'
    LAT_CYR_LOOKALIKES = (('A', 'А'), ('B', 'В'), ('E', 'Е'), ('K', 'К'), ('M', 'М'), ('H', 'Н'), ('O', 'О'), ('P', 'Р'),
                          ('C', 'С'), ('T', 'Т'), ('X', 'Х'), ('Y', 'У'), ('a', 'а'), ('b', 'в'), ('e', 'е'), ('k', 'к'),
                          ('m', 'м'), ('h', 'н'), ('o', 'о'), ('p', 'р'), ('c', 'с'), ('t', 'т'), ('x', 'х'), ('y', 'у'))

    def __init__(self, filepath):
        # read the file
        tree = etree.parse(filepath)
        self.root = tree.getroot()
        time = os.path.getmtime(filepath)
        self.map_datetime = datetime.datetime.fromtimestamp(time).strftime('%H:%M:%S %d/%m/%Y')

    def __search_player(self, playername: str) -> Union[etree.Element, None]:
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

    def __loose_char_equals(self, char1: str, char2: str) -> bool:
        """
        Compare two characters across Cyrillic and Latin alphabets.
        """
        if ord(char1) > ord(char2):
            char1, char2 = char2, char1
        if (char1, char2) in self.LAT_CYR_LOOKALIKES:
            return True
        return char1 == char2

    def loose_char_in(self, char: str, container) -> bool:
        """
        Check if a character is in a container across Cyrillic and Latin alphabets.
        """
        for c in container:
            if self.__loose_char_equals(char, c):
                return True
        return False

    def get_player(self, playername: str, playerID: str) -> Union[player.Player, GetPlayerErrors]:
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

        pl = self.__search_player(playername)
        if not pl:
            return GetPlayerErrors.NOT_FOUND
        name = pl.attrib["name"]
        position = [pl.attrib["x"], pl.attrib["y"]]
        try:
            props = {prop.attrib["name"]: prop.attrib.get("value") or prop.text
                        for prop in pl.find("properties").findall("property")}
        except AttributeError:
            props = {}
        foundPlayerID = props.get("ID игрока", "")
        if str(playerID) != str(foundPlayerID):
            print("Player ID mismatch: expected {}, got {}".format(type(foundPlayerID), type(playerID)))
            return GetPlayerErrors.WRONG_ID
        inventory = []
        for item in props.get("Инвентарь", "").split("\n"):
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
            durability = re.findall(r"\([0-9].?\/[0-9].?\)", item)
            if durability:
                itemDurability, itemMaxDurability = [int(i) for i in durability[0].replace("(", "").replace(")", "").split("/")]
                if itemDurability / itemMaxDurability <= 0.25:
                    durabilityIndex = item.find("(")
                    item = item[:durabilityIndex] + "[31m" + item[durabilityIndex:] + "[0m"
                
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
                        try:
                            props = {prop.attrib["name"]: prop.attrib.get("value")
                                for prop in object.find("properties").findall("property")}
                        except AttributeError:
                            props = {}
                        group = props.get("Группа", "")
                        hidden = True if props.get("Скрыт", "false") == "true" else False
                        owner = props.get("Владелец", "")
                        if  (not hidden) or\
                            (owner != "" and owner == player.name) or\
                            (group != "" and group == player.group) or\
                            (name != "???" and name == player.name):
                            objX, objY = objX % 32 // 4, objY % 32 // 4
                            objects.append((object.attrib.get("name", "???"), objX, objY, object.attrib.get("class", "")))

        return sorted(objects, key=lambda x: x[0]+str(x[1])+str(x[2]))

    def construct_ascii_repr(self, player: player.Player) -> str:
        """
        Generates an ASCII string representation of a room

        :param player: the player object
        :returns: an ASCII string representation of a room
        """
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
            if self.loose_char_in(firstChar, usedChars):
                firstChar = firstChar.lower()
            while self.loose_char_in(firstChar, usedChars):
                firstChar = Map.ASCII_DEFAULT_CHARS[nextDefaultIndex]
                nextDefaultIndex += 1
            if obj[0] == player.name:
                coloredChar = '[2;47m[2;30m' + firstChar + '[0m'
            elif obj[3] == "НПЦ":
                coloredChar = '[2;31m' + firstChar + '[0m'
            elif obj[3] == "Предмет(-ы)":
                coloredChar = '[2;34m' + firstChar + '[0m'
            elif obj[3] == "Игрок":
                coloredChar = '[2;37m' + firstChar + '[0m'
            else:
                coloredChar = firstChar
            repr[obj[2]][obj[1]] = coloredChar
            usedChars.append(firstChar)
            legend[coloredChar] = [obj[0]]
        repr = "\n".join(["".join(row) for row in repr])
        legend = "\n".join([f"{char}: {', '.join(objs)}" for char, objs in legend.items()])
        return f"{repr}\n\n{legend}"

if __name__ == '__main__':
    map = Map("instances-cropped.tmx")
    player = map.get_player("Штрафник Данёк", "236917592684625921")
    print(player.inventory)
