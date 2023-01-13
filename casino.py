import random


CARDS_SUITS = ("\♠️","\♥️","\♣️","\♦️")
CARDS_VALS = ("2","3","4","5","6","7","8","9","10","J","Q","K","A")
CARDS = [v+s for v in CARDS_VALS for s in CARDS_SUITS]

class Blackjack:
    def __init__(self) -> None:
        self.__deck = []
        self.shuffle_deck()

    @property
    def deck(self):
        """
        List of cards
        """
        return self.__deck

    def shuffle_deck(self) -> None:
        """
        Resets and shuffles the deck
        """
        self.__deck = random.sample(CARDS, len(CARDS))

    def draw_card(self) -> str:
        """
        Draws a card from the top of the deck
        :return: a card
        """
        card = self.__deck.pop(0)

        # shuffle the deck when the deck is empty
        if len(self.__deck) == 0:
            self.__deck = self.shuffle_deck()

        return card
