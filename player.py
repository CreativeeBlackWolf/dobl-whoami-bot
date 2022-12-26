class Player:
    def __init__(self, 
                 position:          list, # [x, y]
                 name:              str, 
                 inventory:         list,
                 HP:                str, # HP/MAXHP (TRUE HP)
                 MP:                str, # MP/MAXMP (TRUE MP)
                 SP:                str,
                 level:             str,
                 frags:             str, # frags/frags until levelup
                 active_abilities:  list,
                 passive_abilities: list,
                 rerolls:           str
        ):
        self.position = position
        self.name = name
        self.inventory = inventory
        self.HP = HP
        self.MP = MP
        self.SP = SP
        self.level = level
        self.frags = frags
        self.active_abilities = active_abilities
        self.passive_abilities = passive_abilities
        self.rerolls = rerolls

    def __str__(self):
        return f"Player: {self.name}"
