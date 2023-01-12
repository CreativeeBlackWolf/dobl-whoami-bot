import unittest
import os
import sys
import mapparser
import player


# prepare sys.path for importing modules from parent directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

# ---FLAT LIST:---

# TEXT TYPES:
# [30mBLACK TEXT[0m
# [31mRED TEXT[0m
# [32mGREEN TEXT[0m
# [33mYELLOW TEXT[0m
# [34mBLUE TEXT[0m
# [35mMAGENTA TEXT[0m
# [36mCYAN TEXT[0m
# [37mWHITE TEXT (SIMILAR TO **BOLD** IN NORMAL TEXT)[0m
# [4mUNDERLINED TEXT[0m

# BACKGROUNDS (PREFIXES):
# [40mBLACK BG[0m
# [41mRED BG[0m
# [44mGREY BG[0m
# [45mMAGENTA BG[0m
# [47mWHITE BG[0m
# ([42m42[0m, [43m43[0m, AND [46m46[0m ARE SLIGHTLY DIFFERENT GREYS)

# FINISHER:
# [0m NECESSARY ON EVERY LINE BREAK

class TestPlayer(unittest.TestCase):
    gameMap = mapparser.Map(os.path.join(current, "test.tmx"))

    def test_format_inventory_list(self):
        self.maxDiff = None
        self.assertEqual(self.gameMap.get_player("test_player5", 5).inventory, [""])
        self.assertEqual(player.Player.format_inventory_list(
            [
                "27ж", 
                "1э. test item 1 {???, ???hidden} (1/1)",
                "2. test item 2 {???, shown???hidden, ???(hidden)shown, full} (1/10)",
                "3э. test item 3 (real item name) {something, ???} (2/10)",
                "4. test item 4 {shown, shown2, ???(hidden)shown} (20/20)"
            ]),
            [
                "27ж",
                "[32m1э[0m. test item 1 {[35m???[0m, [35m???[0m} (1/1)",
                "2. test item 2 {[35m???[0m, shown?, ?shown, full} [31m(1/10)[0m",
                "[32m3э[0m. test item 3 {something, [35m???[0m} [31m(2/10)[0m",
                "4. test item 4 {shown, shown2, ?shown} (20/20)"
            ]
        )
