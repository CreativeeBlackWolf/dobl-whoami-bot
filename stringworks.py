LAT_CYR_LOOKALIKES = (('A', 'А'), ('B', 'В'), ('E', 'Е'), ('K', 'К'), ('M', 'М'), ('H', 'Н'), ('O', 'О'), ('P', 'Р'),
                      ('C', 'С'), ('T', 'Т'), ('X', 'Х'), ('Y', 'У'), ('a', 'а'), ('b', 'в'), ('e', 'е'), ('k', 'к'),
                      ('m', 'м'), ('h', 'н'), ('o', 'о'), ('p', 'р'), ('c', 'с'), ('t', 'т'), ('x', 'х'), ('y', 'у'))
UNDERLINE_CODE = '[4;2m'

def loose_char_equals(char1: str, char2: str) -> bool:
    """
    Compare two characters across Cyrillic and Latin alphabets.
    Can also seek for a character in a container, useful for removing ANSI escape sequences.
    """
    assert(len(char1) == 1 or len(char2) == 1)
    if len(char1) > 1:
        return loose_char_in(char2, char1)
    if len(char2) > 1:
        return loose_char_in(char1, char2)
    if ord(char1) > ord(char2):
        char1, char2 = char2, char1
    if (char1, char2) in LAT_CYR_LOOKALIKES:
        return True
    return char1 == char2

def loose_char_in(char: str, container) -> bool:
    """
    Check if a character is in a container across Cyrillic and Latin alphabets.
    """
    for c in container:
        if loose_char_equals(char, c):
            return True
    return False
