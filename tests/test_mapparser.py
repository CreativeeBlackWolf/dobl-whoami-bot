import sys
import os
from colorama import Fore, Back, Style
import stringworks

# prepare sys.path for importing modules from parent directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import mapparser
import unittest
import player
import roomobject

class TestMapParser(unittest.TestCase):
    maxDiff = None

    map = mapparser.Map(os.path.join(current, "test.tmx"))

    def test_get_objects_inventory(self):
        with self.assertRaises(mapparser.MapObjectNotFoundException) as context:
            self.map.get_objects_inventory("not_found")
        self.assertTrue("No object with name `not_found` found." in str(context.exception))

        self.assertEqual(self.map.get_objects_inventory("token_pile"), [f"{Fore.YELLOW}50ж{Style.RESET_ALL}"])
        self.assertEqual(self.map.get_objects_inventory("no_inventory"), [''])

    def test_get_player(self):
        with self.assertRaises(mapparser.MapObjectNotFoundException) as context:
            self.assertEqual(self.map.get_player("not_found", 1), mapparser.MapObjectError.NOT_FOUND)
        self.assertTrue("No object with name `not_found` found." in str(context.exception))

        with self.assertRaises(mapparser.MapObjectWrongIDException) as context:
            self.assertEqual(self.map.get_player("test_player1", 2), mapparser.MapObjectError.WRONG_ID)
        self.assertTrue("ID `1` expected for `test_player1`, got `2`.")

        testPlayerGot = self.map.get_player("test_player1", 1)
        testPlayerActual = player.Player(
            position = ['36', '-216'],
            name = "test_player1",
            inventory = [""],
            active_abilities = [""],
            passive_abilities = [""],
            HP = 100,
            MP = 100,
            SP = 3,
            maxHP = 100,
            maxMP = 100,
            level = 1,
            frags = "0/4",
            trueHP = 100,
            trueMP = 100,
            rerolls = 2,
            group = "группа 1",
            isBlind = False,
            isDead = False
        )
        for attr in testPlayerGot.__dict__:
            self.assertEqual(getattr(testPlayerGot, attr), getattr(testPlayerActual, attr))

    def test_get_same_room_objects(self):
        testPlayer = self.map.get_player("test_player1", 1)
        objectsGot = self.map.get_same_room_objects(testPlayer)
        objectsActual = [
            roomobject.RoomObject('test_player1', (1, 2), (1, 1), 'Игрок', 1),
            roomobject.RoomObject('Турель', (2, 1), (2, 2), 'Структура', 1),
            roomobject.RoomObject('???', (3, 5), (1, 1), 'НПЦ', 1),
            roomobject.RoomObject('test_player2', (4, 2), (1, 1), 'Игрок', 1),
            roomobject.RoomObject('something', (6, 4), (1, 1), '', 1),
            roomobject.RoomObject('item_pile', (1, 6), (1, 1), 'Предмет(-ы)', 0),
            roomobject.RoomObject('test_player3', (5, 7), (1, 1), 'Труп', 0),
            roomobject.RoomObject('Режущая завеса', (2, 1), (1, 3), '', -1)
        ]
        self.assertEqual(objectsGot, objectsActual)

        testPlayer = self.map.get_player("test_player2", 2)
        objectsGot = self.map.get_same_room_objects(testPlayer)
        objectsActual = [
            roomobject.RoomObject('test_player1', (1, 2), (1, 1),  'Игрок', 1),
            roomobject.RoomObject('Турель', (2, 1), (2, 2), 'Структура', 1),
            roomobject.RoomObject('test_player2', (4, 2), (1, 1),  'Игрок', 1),
            roomobject.RoomObject('something', (6, 4), (1, 1),  '', 1),
            roomobject.RoomObject('test_player3', (5, 7), (1, 1),  'Труп', 0),
            roomobject.RoomObject('Режущая завеса', (2, 1), (1, 3), '', -1)
        ]
        self.assertEqual(objectsGot, objectsActual)

    def test_construct_ascii_room(self):
        testPlayer = self.map.get_player("test_player1", 1)
        asciiGot = self.map.construct_ascii_room(testPlayer)
        asciiActual = f"""\
........
..{stringworks.UNDERLINE_CODE}{Fore.YELLOW}Т{Style.RESET_ALL}{Fore.YELLOW}т{Style.RESET_ALL}....
.{Back.WHITE}{Fore.BLACK}!{Style.RESET_ALL}{stringworks.UNDERLINE_CODE}{Fore.YELLOW}Т{Style.RESET_ALL}{Fore.YELLOW}т{Style.RESET_ALL}{Fore.WHITE}\"{Style.RESET_ALL}...
..{stringworks.UNDERLINE_CODE}Р{Style.RESET_ALL}.....
......S.
...{Fore.RED}?{Style.RESET_ALL}....
.{Fore.BLUE}I{Style.RESET_ALL}......
.....{Fore.BLACK}#{Style.RESET_ALL}..

{stringworks.UNDERLINE_CODE}{Fore.YELLOW}Т{Style.RESET_ALL}: Турель, Режущая завеса
{Fore.YELLOW}т{Style.RESET_ALL}: Турель
{Back.WHITE}{Fore.BLACK}!{Style.RESET_ALL}: test_player1
{Fore.WHITE}\"{Style.RESET_ALL}: test_player2
{stringworks.UNDERLINE_CODE}Р{Style.RESET_ALL}: Режущая завеса
S: something
{Fore.RED}?{Style.RESET_ALL}: ???
{Fore.BLUE}I{Style.RESET_ALL}: item_pile
{Fore.BLACK}#{Style.RESET_ALL}: test_player3"""
        self.assertEqual(asciiGot, asciiActual)
        testPlayer = self.map.get_player("test_player5", 5)
        asciiGot = self.map.construct_ascii_room(testPlayer)
        asciiActual = f"""\
........
........
..{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}.....
........
........
........
........
........

{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}: test_player5, dead_body"""
        self.assertEqual(asciiGot, asciiActual)
        testPlayer = self.map.get_player("test_player8", 8)
        asciiGot = self.map.construct_ascii_room(testPlayer)
        asciiActual = f"""\
........
........
........
...{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}....
........
........
......{Fore.WHITE}t{Style.RESET_ALL}.
...{Fore.YELLOW}Л{Style.RESET_ALL}....

{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}: test_player8
{Fore.WHITE}t{Style.RESET_ALL}: test_player12
{Fore.YELLOW}Л{Style.RESET_ALL}: Лестница вниз"""
        self.assertEqual(asciiGot, asciiActual)

    def test_construct_ascii_room_blinded(self):
        testPlayer = self.map.get_player("test_player13", 13)
        asciiGot = self.map.construct_ascii_room(testPlayer)
        asciiActual = f"""\
????????
????????
????????
????????
????????
????????
.{Fore.RED}Г{Style.RESET_ALL}??????
{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}{Fore.RED}Г{Style.RESET_ALL}??????

{Fore.RED}Г{Style.RESET_ALL}: Гигант
{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}: test_player13\
"""
        self.assertEqual(asciiGot, asciiActual)

    def test_list_doors_string(self):
        testPlayer = self.map.get_player("test_player1", 1)
        self.assertEqual(self.map.list_doors_string(testPlayer), "В этой комнате нет дверей.")
        testPlayer = self.map.get_player("test_player6", 6)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Двери ведут на юг и восток.")
        testPlayer = self.map.get_player("test_player7", 7)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Двери ведут на 4 стороны света.")
        testPlayer = self.map.get_player("test_player8", 8)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Единственная дверь ведёт на север.")
        testPlayer = self.map.get_player("test_player9", 9)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Двери ведут на север, запад и восток.")
        testPlayer = self.map.get_player("test_player10", 10)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Единственная дверь ведёт на юг.")
        testPlayer = self.map.get_player("test_player14", 14)
        self.assertEqual(self.map.list_doors_string(testPlayer), "В этой комнате нет дверей?")

    def test_construct_ascii_map(self):
        testPlayer = self.map.get_player("test_player8", 8)
        asciiGot = self.map.construct_ascii_map(testPlayer)
        asciiActual = """\
 ##
 ##
###
## 
 # 


"""
        self.assertEqual(asciiGot, asciiActual)

        testPlayer = self.map.get_player("test_player12", 12)
        asciiGot = self.map.construct_ascii_map(testPlayer, 2)
        asciiActual = f"""\
 П{Style.RESET_ALL}{Fore.RED}Н{Style.RESET_ALL}
 {Fore.RED}Н{Style.RESET_ALL}{Fore.RED}Н{Style.RESET_ALL}
{Fore.YELLOW}Т{Style.RESET_ALL}{Fore.RED}Н{Style.RESET_ALL}{Fore.GREEN}С{Style.RESET_ALL}
{Fore.RED}Н{Style.RESET_ALL}{Fore.YELLOW}Т{Style.RESET_ALL} 
 {Back.WHITE}{Fore.RED}Н{Style.RESET_ALL} 


П{Style.RESET_ALL}: Пусто
{Fore.RED}Н{Style.RESET_ALL}: НПЦ
{Fore.YELLOW}Т{Style.RESET_ALL}: Торговец
{Fore.GREEN}С{Style.RESET_ALL}: Событие
{Back.WHITE} {Style.RESET_ALL}: test_player12\
"""
        self.assertEqual(asciiGot, asciiActual)

        testPlayer = self.map.get_player("test_player10", 10)
        asciiGot = self.map.construct_ascii_map(testPlayer, 1)
        asciiActual = f"""\
 {Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL} 
###
## 
 ##
 # 


{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}: test_player10
#: ???\
"""
        self.assertEqual(asciiGot, asciiActual)

    def test_get_player_floor_coords(self):
        testPlayer = self.map.get_player("test_player5", 5)
        coordsGot = self.map.get_player_floor_coords(testPlayer)
        coordsActual = (4, 0)
        self.assertEqual(coordsGot, coordsActual)
        testPlayer = self.map.get_player("test_player6", 6)
        coordsGot = self.map.get_player_floor_coords(testPlayer)
        coordsActual = (1, 0)
        self.assertEqual(coordsGot, coordsActual)
        testPlayer = self.map.get_player("test_player7", 7)
        coordsGot = self.map.get_player_floor_coords(testPlayer)
        coordsActual = (1, 2)
        self.assertEqual(coordsGot, coordsActual)
        testPlayer = self.map.get_player("test_player8", 8)
        coordsGot = self.map.get_player_floor_coords(testPlayer)
        coordsActual = (1, 4)
        self.assertEqual(coordsGot, coordsActual)
        testPlayer = self.map.get_player("test_player9", 9)
        coordsGot = self.map.get_player_floor_coords(testPlayer)
        coordsActual = (1, 1)
        self.assertEqual(coordsGot, coordsActual)
        testPlayer = self.map.get_player("test_player10", 10)
        coordsGot = self.map.get_player_floor_coords(testPlayer)
        coordsActual = (1, 0)
        self.assertEqual(coordsGot, coordsActual)

    def test_get_floor_string(self):
        testPlayer = self.map.get_player("test_player5", 5)
        floorStringGot = self.map.get_floor_string(testPlayer)
        floorStringActual = 'Ты находишься в локации "testarea".'
        self.assertEqual(floorStringGot, floorStringActual)
        testPlayer = self.map.get_player("test_player15", 15)
        floorStringGot = self.map.get_floor_string(testPlayer)
        floorStringActual = 'Ты находишься на 1 этаже 1 инстанса.'
        self.assertEqual(floorStringGot, floorStringActual)
        testPlayer = self.map.get_player("test_player17", 17)
        floorStringGot = self.map.get_floor_string(testPlayer)
        floorStringActual = 'Неясно, где ты находишься.'
        self.assertEqual(floorStringGot, floorStringActual)
        testPlayer = self.map.get_player("test_player18", 18)
        floorStringGot = self.map.get_floor_string(testPlayer)
        floorStringActual = 'Неясно, где ты находишься.'
        self.assertEqual(floorStringGot, floorStringActual)
        testPlayer = self.map.get_player("test_player9", 9)
        floorStringGot = self.map.get_floor_string(testPlayer)
        floorStringActual = 'Ты находишься на 1 этаже 4 инстанса.'
        self.assertEqual(floorStringGot, floorStringActual)

if __name__ == '__main__':
    unittest.main()
