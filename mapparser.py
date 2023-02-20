from __future__ import annotations
from typing import Union
from enum import Enum
import defusedxml.ElementTree as defused_etree
import xml.etree.ElementTree as etree
import os
import datetime
from colorama import Fore, Back, Style
import player
import floor
import roomobject
import stringworks


class MapObjectException(Exception): pass
class MapObjectNotFoundException(MapObjectException): pass
class MapObjectWrongIDException(MapObjectException): pass


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

    def __init__(self, filepath: str):
        # read the file
        tree = defused_etree.parse(filepath)
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
            if objectgroup.attrib["name"] in ["нижний", "средний", "верхний"] or \
                objectgroup.attrib["name"].startswith("эффекты"):
                for obj in objectgroup.findall("object"):
                    try:
                        if obj.attrib["name"] == objectname:
                            return obj
                    except KeyError:
                        pass

    def get_objects_inventory(
            self, 
            objectname: str, 
            show_equipped_only: bool = False
        ) -> list:
        """
        Get formatted inventory of a given object by name
        :param objectname: name of the object
        :param show_equipped_only: return only equipped items
        :return: formatted inventory
        :raises: MapObjectNotFoundException if the object does not found
        """
        obj = self.__search_object(objectname)

        if obj is None:
            raise MapObjectNotFoundException(f"No object with name `{objectname}` found.")

        try:
            props = {prop.attrib["name"]: prop.attrib.get("value") or prop.text
                        for prop in obj.find("properties").findall("property")}
        except AttributeError:
            props = {}

        return player.Player.format_inventory_list(props.get("Инвентарь", "").split("\n"), show_equipped_only)

    def get_player(self, playername: str, playerID: str) -> player.Player:
        """
        Get serialized Player object

        :param playername: the name of the player to search for
        :param playerID: Discord id of the player
        :return: player.Player object
        :raises: MapObjectNotFoundException if player not found
        :raises: MapObjectWrongIDException if expected playerID
        """
        pl = self.__search_object(playername)
        if not pl:
            raise MapObjectNotFoundException(f"No object with name `{playername}` found.")

        name = pl.attrib["name"]
        position = [pl.attrib["x"], pl.attrib["y"]]
        try:
            props = {prop.attrib["name"]: prop.attrib.get("value") or prop.text
                        for prop in pl.find("properties").findall("property")}
        except AttributeError:
            props = {}

        foundPlayerID = props.get("ID игрока", "")
        if str(playerID) != str(foundPlayerID):
            raise MapObjectWrongIDException(f"ID `{foundPlayerID}` expected for `{playername}`, " +
                                            f"got {playerID} instead.")

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
        isBlind           = props.get("Ослеплён", "false").lower() in ["true", "1"]
        isDead            = pl.attrib.get("class", "Игрок").lower() == "труп"
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
            group=group,
            isBlind=isBlind,
            isDead=isDead
        )

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
            if objectgroup.attrib["name"] in ["нижний", "средний", "верхний"] or \
               objectgroup.attrib["name"].startswith("эффекты"):
                for obj in objectgroup.findall("object"):
                    objX, objY = int(obj.attrib["x"]), int(obj.attrib["y"])
                    if objX-objX % 32 == roomPos[0] and objY-objY % 32 == roomPos[1]:
                        name = obj.attrib.get("name", "???")
                        try:
                            props = {prop.attrib["name"]: prop.attrib.get("value")
                                for prop in obj.find("properties").findall("property")}
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
                            width = int(obj.attrib.get("width", 0)) // 4
                            height = int(obj.attrib.get("height", 0)) // 4
                            layer = objectgroup.attrib["name"]
                            obj = roomobject.RoomObject(obj.attrib.get("name", "???"),
                                                        (objX, objY),
                                                        (width, height),
                                                        obj.attrib.get("class", ""),
                                                        layer)
                            objects.append(obj)

        return sorted(objects, key=lambda x: [-x.layer, x.position[0], x.position[1]])

    def construct_ascii_room(self, player: player.Player) -> str:
        """
        Generates an ASCII string representation of a room

        :param player: the player object
        :returns: an ASCII string representation of a room
        """
        objlist = self.get_same_room_objects(player)
        playerPos = [ int(player.position[0]) % 32 // 4,
                      int(player.position[1]) % 32 // 4]
        tileContents = [ [ [] for x in range(8) ] for y in range(8) ]
        for obj in objlist:
            for x in range(obj.size[0]):
                for y in range(obj.size[1]):
                    if player.isBlind:
                        if obj.position[0]+x - playerPos[0] in range(-1, 2) and \
                           obj.position[1]+y - playerPos[1] in range(-1, 2):
                            pass
                        else:
                            continue
                    tileContents[obj.position[1]+y][obj.position[0]+x].append(obj)
        usedChars = {}
        legend = {}
        nextDefaultIndex = 0
        for y in range(8):
            for x in range(8):
                if len(tileContents[y][x]) == 0:
                    continue
                # check if there is a char already used for this combo
                skip = False
                for _, combo in usedChars.values():
                    if combo == tileContents[y][x]:
                        skip = True
                        break
                if skip:
                    continue
                # find a new char, first candidate is the first letter of an object name
                firstCharObj = tileContents[y][x][0]
                for obj in tileContents[y][x]:
                    if obj.name == player.name:
                        # prioritize the player
                        firstCharObj = obj
                        break
                    if obj.layer > firstCharObj.layer:
                        # prioritize objects on higher layers
                        firstCharObj = obj
                effectPresent = False
                for obj in tileContents[y][x]:
                    if obj.layer < 0:
                        effectPresent = True
                        break
                firstChar = firstCharObj.name[0].upper()
                if stringworks.loose_char_in(firstChar, usedChars):
                    firstChar = firstChar.lower()
                while stringworks.loose_char_in(firstChar, usedChars):
                    firstChar = Map.ASCII_DEFAULT_CHARS[nextDefaultIndex]
                    nextDefaultIndex += 1
                isReset = True
                # colorize the char
                if firstCharObj.name == player.name:
                    coloredChar = f'{Back.WHITE}{Fore.BLACK}' + firstChar + Style.RESET_ALL
                elif firstCharObj.obj_class == "НПЦ":
                    coloredChar = Fore.RED + firstChar + Style.RESET_ALL
                elif firstCharObj.obj_class == "Предмет(-ы)":
                    coloredChar = Fore.BLUE + firstChar + Style.RESET_ALL
                elif firstCharObj.obj_class == "Игрок":
                    coloredChar = Fore.WHITE + firstChar + Style.RESET_ALL
                elif firstCharObj.obj_class == "Труп":
                    coloredChar = Fore.BLACK + firstChar + Style.RESET_ALL
                elif firstCharObj.obj_class == "Структура":
                    coloredChar = Fore.YELLOW + firstChar + Style.RESET_ALL
                else:
                    coloredChar = firstChar
                    isReset = False
                if effectPresent:
                    # underline the char, looks like colorama doesn't support underlined text?
                    coloredChar = stringworks.UNDERLINE_CODE + coloredChar
                    if not isReset:
                        coloredChar += Style.RESET_ALL
                usedChars[firstChar] = (coloredChar, tileContents[y][x])
                legend[coloredChar] = [obj.name for obj in tileContents[y][x]]
        representation = [
            [
                "."
                if not player.isBlind or
                      (player.isBlind and (x - playerPos[0] in range(-1, 2) and y - playerPos[1] in range(-1, 2)))
                else "?"
                for x in range(8)
            ]
            for y in range(8)
        ]
        for y in range(8):
            for x in range(8):
                if len(tileContents[y][x]) == 0:
                    continue
                for _, charObjTuple in usedChars.items():
                    if tileContents[y][x] == charObjTuple[1]:
                        representation[y][x] = charObjTuple[0]
                        break
        representation = "\n".join(["".join(row) for row in representation])
        legend = "\n".join([f"{char}: {', '.join(objs)}" for char, objs in legend.items()])
        return f"{representation}\n\n{legend}"

    def __list_doors(self, player: player.Player) -> list:
        """
        List available doors in the same room as the player

        :param player: the player in question
        :return: list of doors
        """
        roomPos = [ int(player.position[0]) // 32,
                    int(player.position[1]) // 32]
        playerPos = [ int(player.position[0]) % 32 // 4,
                      int(player.position[1]) % 32 // 4]
        floor = self.__get_floor_player(player)
        if floor is None:
            return []
        doors = []
        if self.__get_tile([roomPos[0], roomPos[1]-1]) not in (TileIDs.NULL, TileIDs.ABYSS) and \
            getattr(self.__get_floor_tile((roomPos[0], roomPos[1]-1)), "name", None) == floor.name:
            if player.isBlind:
                if playerPos[1] == 0:
                    doors.append("север")
            else:
                doors.append("север")
        if self.__get_tile([roomPos[0], roomPos[1]+1]) not in (TileIDs.NULL, TileIDs.ABYSS) and \
            getattr(self.__get_floor_tile((roomPos[0], roomPos[1]+1)), "name", None) == floor.name:
            if player.isBlind:
                if playerPos[1] == 7:
                    doors.append("юг")
            else:
                doors.append("юг")
        if self.__get_tile([roomPos[0]-1, roomPos[1]]) not in (TileIDs.NULL, TileIDs.ABYSS) and \
            getattr(self.__get_floor_tile((roomPos[0]-1, roomPos[1])), "name", None) == floor.name:
            if player.isBlind:
                if playerPos[0] == 0:
                    doors.append("запад")
            else:
                doors.append("запад")
        if self.__get_tile([roomPos[0]+1, roomPos[1]]) not in (TileIDs.NULL, TileIDs.ABYSS) and \
            getattr(self.__get_floor_tile((roomPos[0]+1, roomPos[1])), "name", None) == floor.name:
            if player.isBlind:
                if playerPos[0] == 7:
                    doors.append("восток")
            else:
                doors.append("восток")
        return doors

    def list_doors_string(self, player: player.Player) -> str:
        """
        List available doors in the same room as the player

        :param player: the player in question
        :return: friendly string describing available doors
        """
        doors = self.__list_doors(player)
        if len(doors) == 0:
            resp = "В этой комнате нет дверей" + ("?" if player.isBlind else ".")
        elif len(doors) == 1:
            resp = f"Единственная дверь ведёт на {doors[0]}."
        elif len(doors) == 2:
            resp = f"Двери ведут на {doors[0]} и {doors[1]}."
        elif len(doors) == 3:
            resp = f"Двери ведут на {doors[0]}, {doors[1]} и {doors[2]}."
        elif len(doors) == 4:
            resp = "Двери ведут на 4 стороны света."
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

    def construct_ascii_map(self, player: player.Player, level: int = 0) -> str:
        """
        Construct the map of a floor the player is in, represented as ASCII art

        :param player: the player in question
        :return: the map
        """
        floor = self.__get_floor_player(player)
        if floor is None:
            return "Карта пуста."
        floorStart = [floor.start[0] // 32, floor.start[1] // 32]
        floorSize = [floor.size[0] // 32, floor.size[1] // 32]
        representation = ''
        legend = {}
        for y in range(floorSize[1]):
            for x in range(floorSize[0]):
                tile = self.__get_tile([floorStart[0]+x, floorStart[1]+y])
                character = Back.WHITE if level >= 2 and self.get_player_floor_coords(player) == (x, y) else ""
                if tile in (TileIDs.NULL, TileIDs.ABYSS):
                    representation += ' '
                elif level >= 2 and tile == TileIDs.EVENT:
                    character += Fore.GREEN + "С" + Style.RESET_ALL
                    representation += character
                    legend[Fore.GREEN + "С" + Style.RESET_ALL] = "Событие"
                elif level >= 2 and tile == TileIDs.ENEMY:
                    character += Fore.RED + "Н" + Style.RESET_ALL
                    representation += character
                    legend[Fore.RED + "Н" + Style.RESET_ALL] = "НПЦ"
                elif level >= 2 and tile == TileIDs.MERCHANT:
                    character += Fore.YELLOW + "Т" + Style.RESET_ALL
                    representation += character
                    legend[Fore.YELLOW + "Т" + Style.RESET_ALL] = "Торговец"
                elif level >= 2 and tile == TileIDs.EMPTY:
                    character += "П" + Style.RESET_ALL
                    representation += character
                    legend["П" + Style.RESET_ALL] = "Пусто"
                elif level == 1 and self.get_player_floor_coords(player) == (x, y):
                    chararter = Back.WHITE + Fore.BLACK + player.name[0].upper() + Style.RESET_ALL
                    representation += chararter
                    legend[chararter] = player.name
                else:
                    representation += '#'
                    legend["#"] = "???"

                if character.startswith(Back.WHITE):
                    legend[f"{Back.WHITE} {Style.RESET_ALL}"] = player.name

            representation += '\n'
        legend = "\n".join([f"{char}: {''.join(objs)}" for char, objs in legend.items()])
        return f"{representation}\n\n{legend if level > 0 else ''}"

    def get_player_floor_coords(self, player: player.Player) -> tuple[int, int]:
        """
        Get the coordinates of the player relative to the floor

        :param player: the player in question
        :return: the coordinates
        """
        roomPos = [ int(player.position[0]) // 32,
                    int(player.position[1]) // 32]
        floor = self.__get_floor_player(player)
        floorStart = [floor.start[0] // 32, floor.start[1] // 32]
        return (roomPos[0]-floorStart[0], roomPos[1]-floorStart[1])

    def __get_floor_px(self, objPos) -> floor.Floor:
        """
        Get the floor at given coordinates (in px)

        :param objPos: object's position (in px)
        :return: the floor or None if not on a floor
        """
        for objectgroup in self.root.findall("objectgroup"):
            if objectgroup.attrib["name"] == "этажи":
                for obj in objectgroup.findall("object"):
                    startX, startY = int(obj.attrib["x"]), int(obj.attrib["y"])
                    sizeX, sizeY = int(obj.attrib["width"]), int(obj.attrib["height"])
                    if  startX <= objPos[0] and \
                        startY <= objPos[1] and \
                        startX + sizeX > objPos[0] and \
                        startY + sizeY > objPos[1]:
                        name = obj.attrib.get("name", "???")
                        return floor.Floor((startX, startY), (sizeX, sizeY), name)

    def __get_floor_tile(self, tilePos) -> floor.Floor:
        """
        Get the floor at given coordinates (in tiles)

        :param tilePos: object's position (in tiles)
        :return: the floor or None if not on a floor
        """
        return self.__get_floor_px([tilePos[0]*32, tilePos[1]*32])

    def __get_floor_player(self, player: player.Player) -> floor.Floor:
        """
        Get the floor the player is on

        :param player: the player in question
        :return: the floor
        """
        return self.__get_floor_px((int(player.position[0]), int(player.position[1])))

    def get_floor_string(self, player: player.Player) -> str:
        """
        Get the name of the floor the player is on, pretty-printed

        :param player: the player in question
        :return: the name
        """
        floor = self.__get_floor_player(player)
        if floor is None:
            return "Неясно, где ты находишься."
        if not floor.instance is None:
            if not floor.number is None:
                return f"Ты находишься на {floor.number} этаже {floor.instance} инстанса."
            return f"Ты находишься где-то в {floor.instance} инстансе."
        if not floor.number is None:
            return f"Ты находишься на {floor.number} этаже в неизвестном инстансе."
        if floor.name != "???":
            return f'Ты находишься в локации "{floor.name}".'
        return "Неясно, где ты находишься."
