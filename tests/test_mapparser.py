import sys
import os

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

        self.assertEqual(self.map.get_objects_inventory("token_pile"), ["50ж"])
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
            group = "группа 1"
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

    def test_construct_ascii_repr(self):
        testPlayer = self.map.get_player("test_player1", 1)
        asciiGot = self.map.construct_ascii_repr(testPlayer)
        asciiActual = """\
........
........
.[2;47m[2;30mT[0m..[2;37mt[0m...
........
......S.
...[2;31m?[0m....
.[2;34mI[0m......
.....[2;30m![0m..

[2;31m?[0m: ???
[2;34mI[0m: item_pile
S: something
[2;47m[2;30mT[0m: test_player1
[2;37mt[0m: test_player2
[2;30m![0m: test_player3"""
        self.assertEqual(asciiGot, asciiActual)
        testPlayer = self.map.get_player("test_player5", 5)
        asciiGot = self.map.construct_ascii_repr(testPlayer)
        asciiActual = """\
........
........
..[2;47m[2;30mD[0m.....
........
........
........
........
........

[2;47m[2;30mD[0m: dead_body, test_player5"""
        self.assertEqual(asciiGot, asciiActual)

    def test_list_doors_string(self):
        testPlayer = self.map.get_player("test_player1", 1)
        self.assertEqual(self.map.list_doors_string(testPlayer), "В этой комнате нет дверей.")
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

if __name__ == '__main__':
    unittest.main()
