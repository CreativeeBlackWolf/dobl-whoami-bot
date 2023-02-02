from dataclasses import dataclass
from typing import Union

@dataclass
class RoomObject:
    name: str
    position: tuple[int, int]
    size: tuple[int, int]
    obj_class: str
    layer: Union[str, int]

    def __post_init__(self):
        if isinstance(self.layer, str):
            if self.layer == "нижний":
                self.layer = 0
            elif self.layer == "средний":
                self.layer = 1
            elif self.layer == "верхний":
                self.layer = 2
            elif self.layer.startswith("эффекты"):
                self.layer = -int(self.layer[7:])
            else:
                raise ValueError("Unknown layer: "+self.layer)
        elif self.layer > 2:
            raise ValueError("Unknown layer: "+str(self.layer))
