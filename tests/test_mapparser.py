import sys
import os
from colorama import Fore, Back, Style

# prepare sys.path for importing modules from parent directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import mapparser
import unittest
import player

class TestMapParser(unittest.TestCase):
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
            ('???', 3, 5, 'НПЦ'),
            ('item_pile', 1, 6, 'Предмет(-ы)'),
            ('something', 6, 4, ''),
            ('test_player1', 1, 2, 'Игрок'),
            ('test_player2', 4, 2, 'Игрок'),
            ('test_player3', 5, 7, 'Труп')
        ]
        self.assertEqual(objectsGot, objectsActual)
        testPlayer = self.map.get_player("test_player2", 2)
        objectsGot = self.map.get_same_room_objects(testPlayer)
        objectsActual = [
            ('something', 6, 4, ''),
            ('test_player1', 1, 2, 'Игрок'),
            ('test_player2', 4, 2, 'Игрок'),
            ('test_player3', 5, 7, 'Труп')
        ]
        self.assertEqual(objectsGot, objectsActual)

    def test_construct_ascii_room(self):
        testPlayer = self.map.get_player("test_player1", 1)
        asciiGot = self.map.construct_ascii_room(testPlayer)
        asciiActual = f"""\
........
........
.{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}..{Fore.WHITE}t{Style.RESET_ALL}...
........
......S.
...{Fore.RED}?{Style.RESET_ALL}....
.{Fore.BLUE}I{Style.RESET_ALL}......
.....{Fore.BLACK}!{Style.RESET_ALL}..

{Fore.RED}?{Style.RESET_ALL}: ???
{Fore.BLUE}I{Style.RESET_ALL}: item_pile
S: something
{Back.WHITE}{Fore.BLACK}T{Style.RESET_ALL}: test_player1
{Fore.WHITE}t{Style.RESET_ALL}: test_player2
{Fore.BLACK}!{Style.RESET_ALL}: test_player3"""
        self.assertEqual(asciiGot, asciiActual)
        testPlayer = self.map.get_player("test_player5", 5)
        asciiGot = self.map.construct_ascii_room(testPlayer)
        asciiActual = f"""\
........
........
..{Back.WHITE}{Fore.BLACK}D{Style.RESET_ALL}.....
........
........
........
........
........

{Back.WHITE}{Fore.BLACK}D{Style.RESET_ALL}: dead_body, test_player5"""
        self.assertEqual(asciiGot, asciiActual)

    def test_list_doors_string(self):
        testPlayer = self.map.get_player("test_player1", 1)
        self.assertEqual(self.map.list_doors_string(testPlayer), "В этой комнате нет дверей?")
        testPlayer = self.map.get_player("test_player6", 6)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Двери ведут на юг и восток.")
        testPlayer = self.map.get_player("test_player7", 7)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Двери ведут на 4 стороны света.")
        testPlayer = self.map.get_player("test_player8", 8)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Единственная дверь ведёт на север. Здесь также находится лестница вниз.")
        testPlayer = self.map.get_player("test_player9", 9)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Двери ведут на север, запад и восток.")
        testPlayer = self.map.get_player("test_player10", 10)
        self.assertEqual(self.map.list_doors_string(testPlayer), "Единственная дверь ведёт на юг.")

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
{Fore.YELLOW}Т{Style.RESET_ALL}: Торговец/Казино
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

if __name__ == '__main__':
    unittest.main()
