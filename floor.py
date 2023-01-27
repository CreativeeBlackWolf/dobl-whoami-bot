import re

class Floor:
    def __init__(self,
                 start:     tuple[int, int],
                 size:      tuple[int, int],
                 name:      str):
        self.start = start
        self.name = name
        self.size = size
        self.end = (start[0] + size[0], start[1] + size[1]) # non-inclusive
        parsed = re.findall(r"Этаж (\d+)-(\d+)", name)
        if parsed:
            self.number = int(parsed[0][0])
            self.instance = int(parsed[0][1])
        else:
            self.number = None
            self.instance = None