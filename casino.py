import random


class Blackjack:
    CARDS = {
        "2S" :  "2♠️", "2H" :  "2❤️", "2C" :  "2♣️", "2D" :  "2♦️",
        "3S" :  "3♠️", "3H" :  "3❤️", "3C" :  "3♣️", "3D" :  "3♦️",
        "4S" :  "4♠️", "4H" :  "4❤️", "4C" :  "4♣️", "4D" :  "4♦️",
        "5S" :  "5♠️", "5H" :  "5❤️", "5C" :  "5♣️", "5D" :  "5♦️",
        "6S" :  "6♠️", "6H" :  "6❤️", "6C" :  "6♣️", "6D" :  "6♦️",
        "7S" :  "7♠️", "7H" :  "7❤️", "7C" :  "7♣️", "7D" :  "7♦️",
        "8S" :  "8♠️", "8H" :  "8❤️", "8C" :  "8♣️", "8D" :  "8♦️",
        "9S" :  "9♠️", "9H" :  "9❤️", "9C" :  "9♣️", "9D" :  "9♦️",
        "10S": "10♠️", "10H": "10❤️", "10C": "10♣️", "10D": "10♦️",
        "JS" :  "J♠️", "JH" :  "J❤️", "JC" :  "J♣️", "JD" :  "J♦️",
        "QS" :  "Q♠️", "QH" :  "Q❤️", "QC" :  "Q♣️", "QD" :  "Q♦️",
        "KS" :  "K♠️", "KH" :  "K❤️", "KC" :  "K♣️", "KD" :  "K♦️",
        "AS" :  "A♠️", "AH" :  "A❤️", "AC" :  "A♣️", "AD" :  "A♦️",
    }

    def __init__(self) -> None:
        self.__deck = self.shuffle()

    @property
    def deck(self):
        """
        List of cards, containing all the cards like [(cardname, cardrepr), ...]
        """
        return self.__deck

    def shuffle(self) -> list[tuple[str, str]]:
        """
        Shuffles the deck
        :return: list of tuples containing card name as the first element\
                 and representation of a card as the second element
        """
        return random.sample(list(self.CARDS.items()), len(self.CARDS.items()))

    def draw_card(self) -> tuple[str, str]:
        """
        Draws a card from the top of the deck
        :return: tuple containing card name as the first element\
                 and representation of a card as the second element
        """
        card = self.__deck.pop(0)

        # shuffle the deck when the deck is empty
        if len(self.__deck) == 0:
            self.__deck = self.shuffle()
        
        return card
    
if __name__ == "__main__":
    bj = Blackjack()
    print(bj.deck)
    for _ in range(10):
        print(bj.draw_card())
