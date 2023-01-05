from typing import Union
from enum import Enum
import xml.etree.ElementTree as etree
import os
import datetime
import player


class MapObjectError(Enum):
    NOT_FOUND = "NOT_FOUND"
    WRONG_ID = "WRONG_ID"


class TileIDs(Enum):
    NULL = 0
    EMPTY = 1
    ABYSS = 2
    ENEMY = 3
    MERCHANT = 4
    EVENT = 5

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

    def __search_object(self, objectname: str) -> Union[etree.Element, None]:
        """
        Search for a object in the map.

        :param objectname: the name of the object to search for
        :return: the object's root element or None if no match found
        """
        for objectgroup in self.root.findall("objectgroup"):
            if objectgroup.attrib["name"] in ["нижний", "средний", "верхний"]:
                for object in objectgroup.findall("object"):
                    if object.attrib["name"] == objectname:
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

    def __loose_char_in(self, char: str, container) -> bool:
        """
        Check if a character is in a container across Cyrillic and Latin alphabets.
        """
        for c in container:
            if self.__loose_char_equals(char, c):
                return True
        return False

    def get_objects_inventory(self, objectname: str) -> Union[list, MapObjectError]:
        """
        Get formatted inventory of a given object by name
        :param objectname: name of the object
        :return: formatted inventory
        """
        obj = self.__search_object(objectname)

        if obj is None:
            return MapObjectError.NOT_FOUND

        try:
            props = {prop.attrib["name"]: prop.attrib.get("value") or prop.text
                        for prop in obj.find("properties").findall("property")}
        except AttributeError:
            props = {}

        return player.Player.format_inventory_list(props.get("Инвентарь", "").split("\n"))


    def get_player(self, playername: str, playerID: str) -> Union[player.Player, MapObjectError]:
        """
        Get serialized Player object

        :param playername: the name of the player to search for
        :param playerID: Discord id of the player
        :return: Player object or None if player not found
        """
        pl = self.__search_object(playername)
        if not pl:
            return MapObjectError.NOT_FOUND
        name = pl.attrib["name"]
        position = [pl.attrib["x"], pl.attrib["y"]]
        try:
            props = {prop.attrib["name"]: prop.attrib.get("value") or prop.text
                        for prop in pl.find("properties").findall("property")}
        except AttributeError:
            props = {}

        foundPlayerID = props.get("ID игрока", "")
        if str(playerID) != str(foundPlayerID):
            return MapObjectError.WRONG_ID

        inventory = player.Player.format_inventory_list(props.get("Инвентарь", "").split("\n"))

        hpString          = props.get("Очки Здоровья", "100/100 (100)")
        hp                = int(hpString.split()[0].split("/")[0])
        maxHP             = float(hpString.split()[0].split("/")[1])
        trueHP            = int(hpString.split()[1][1:-1])
        mpString          = props.get("Очки Маны", "100/100 (100)")
        mp                = int(mpString.split()[0].split("/")[0])
        maxMP             = float(mpString.split()[0].split("/")[1])
        trueMP            = int(mpString.split()[1][1:-1])
        sp                = float(props.get("Очки Души", "3"))
        rerolls           = int(props.get("Рероллы", "2"))
        active_abilities  = props.get("Навыки", "").split("\n")
        passive_abilities = props.get("Особенности", "").split("\n")
        level             = int(props.get("Уровень", "1"))
        frags             = props.get("Фраги", "0/4")
        group             = props.get("Группа", "")
        return player.Player(
            position=position,
            name=name,
            inventory=inventory,
            HP=hp,
            maxHP=maxHP,
            trueHP=trueHP,
            MP=mp,
            maxMP=maxMP,
            trueMP=trueMP,
            SP=sp,
            level=level,
            frags=frags,
            active_abilities=active_abilities,
            passive_abilities=passive_abilities,
            rerolls=rerolls,
            group=group)

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
                        if  (not hidden) or \
                            (owner != "" and owner == player.name) or \
                            (group != "" and group == player.group) or \
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
                # if this is the player, colorize the char
                if obj[0] == player.name:
                    coloredChar = '[2;47m[2;30m' + existingChar + '[0m'
                    repr[obj[2]][obj[1]] = coloredChar
                    legend[coloredChar] = legend[existingChar]+[obj[0]]
                    del legend[existingChar]
                else:
                    legend[existingChar].append(obj[0])
                continue
            # find a new char, first candidate is the first letter of the object name
            firstChar = obj[0][0].upper()
            if self.__loose_char_in(firstChar, usedChars):
                firstChar = firstChar.lower()
            while self.__loose_char_in(firstChar, usedChars):
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
            elif obj[3] == "Труп":
                coloredChar = '[2;30m' + firstChar + '[0m'
            else:
                coloredChar = firstChar
            repr[obj[2]][obj[1]] = coloredChar
            usedChars.append(firstChar)
            legend[coloredChar] = [obj[0]]
        repr = "\n".join(["".join(row) for row in repr])
        legend = "\n".join([f"{char}: {', '.join(objs)}" for char, objs in legend.items()])
        return f"{repr}\n\n{legend}"

    def __list_doors(self, player: player.Player) -> list:
        """
        List available doors in the same room as the player

        :param player: the player in question
        :return: list of doors
        """
        roomPos = [ int(player.position[0]) // 32,
                    int(player.position[1]) // 32]
        doors = []
        if self.__get_tile([roomPos[0], roomPos[1]-1]) not in (TileIDs.NULL, TileIDs.ABYSS) and not (
                roomPos[0] % 4 == 0 and
                roomPos[1] % 5 == 1):
            doors.append("север")
        if self.__get_tile([roomPos[0], roomPos[1]+1]) not in (TileIDs.NULL, TileIDs.ABYSS):
            doors.append("юг")
        if self.__get_tile([roomPos[0]-1, roomPos[1]]) not in (TileIDs.NULL, TileIDs.ABYSS):
            doors.append("запад")
        if self.__get_tile([roomPos[0]+1, roomPos[1]]) not in (TileIDs.NULL, TileIDs.ABYSS):
            doors.append("восток")
        # end of floor
        if roomPos[0] % 4 == 0 and roomPos[1] % 5 == 0:
            doors.append("вниз")
        return doors

    def list_doors_string(self, player: player.Player) -> str:
        """
        List available doors in the same room as the player

        :param player: the player in question
        :return: friendly string describing available doors
        """
        doors = self.__list_doors(player)
        if 'вниз' in doors:
            ladder = True
        else:
            ladder = False
        doors = [door for door in doors if door != 'вниз']
        if len(doors) == 0:
            resp = "В этой комнате нет дверей."
        elif len(doors) == 1:
            resp = f"Единственная дверь ведёт на {doors[0]}."
        elif len(doors) == 2:
            resp = f"Двери ведут на {doors[0]} и {doors[1]}."
        elif len(doors) == 3:
            resp = f"Двери ведут на {doors[0]}, {doors[1]} и {doors[2]}."
        elif len(doors) == 4:
            resp = "Двери ведут на 4 стороны света."
        resp = resp if not ladder else resp + " Здесь также находится лестница вниз."
        return resp
    
    def __get_tile(self, pos: list) -> TileIDs:
        """
        Get tile ID at given position

        :param pos: the position
        :returns: tile ID
        """
        chunkPos = [int(pos[0])-int(pos[0]) % 16,
                    int(pos[1])-int(pos[1]) % 16]
        for layer in self.root.findall("layer"):
            if layer.attrib["name"] == "пол":
                for chunk in layer.find('data').findall("chunk"):
                    if chunk.attrib["x"] == str(chunkPos[0]) and chunk.attrib["y"] == str(chunkPos[1]):
                        data = chunk.text
                        data = data.replace("\n", "")
                        data = data.replace(" ", "")
                        data = data.split(",")
                        data = [int(tile) for tile in data]
                        return TileIDs(data[(pos[1] % 16) * 16 + pos[0] % 16])
        raise Exception("Unknown tile at position " + str(pos))

    def construct_ascii_map(self, player: player.Player) -> str:
        """
        Construct the map of a floor the player is in, represented as ASCII art

        :param player: the player in question
        :return: the map
        """
        roomPos = [ int(player.position[0]) // 32,
                    int(player.position[1]) // 32]
        floorStart = [  roomPos[0] - (roomPos[0]+1) % 4,
                        roomPos[1] - (roomPos[1]+4) % 5]
        repr = ''
        for y in range(5):
            for x in range(3):
                tile = self.__get_tile([floorStart[0]+x, floorStart[1]+y])
                if tile in (TileIDs.NULL, TileIDs.ABYSS):
                    repr += ' '
                else:
                    repr += '#'
            repr += '\n'
        tile = self.__get_tile([floorStart[0]+1, floorStart[1]+4])
        return repr