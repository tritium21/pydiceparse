import enum
import itertools
import random


class Suit(enum.Enum):
    Hearts = "♥"
    Spades = "♠"
    Clubs = "♣"
    Diamonds = "♦"


class Joker(enum.Enum):
    Red = "Red Joker"
    Black = "Black Joker"

class Value(enum.IntEnum):
    Ace = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5
    Six = 6
    Seven = 7
    Eight = 8
    Nine = 9
    Ten = 10
    Jack = 11
    Queen = 12
    King = 13


class Card:
    def __init__(self, suit=None, value=None, joker=False):
        self.joker = joker
        if self.joker:
            self.suit, self.value = None, None
        else:
            if value is None:
                self.suit, self.value = suit
            else:
                self.suit = suit
                self.value = value

    def __repr__(self):
        return (
            f"Card(joker={self.joker})" if self.joker else f"Card({self.suit!r}, {self.value!r})"
        )

    def __str__(self):
        return f"{self.joker.value}" if self.joker else f"{self.value.name} of {self.suit.value} {self.suit.name}"


class Deck:
    def __init__(self, include_jokers=True):
        self._include_jokers = include_jokers
        self._discard = []
        self._deck = []
        self.reset()
        
    def reset(self):
        self._discard.clear()
        self._deck[:] = list(
            map(
                Card,
                itertools.product(
                    Suit.__members__.values(), Value.__members__.values()
                ),
            )
        )
        if self._include_jokers:
            self._deck.extend(
                Card(joker=v) for v in Joker.__members__.values()
            )

    def pick(self, count=1, rng=random):
        """
        Select <count> random cards from the deck, and replace them exactly where they were
        """
        return rng.sample(self._deck, count)

    def shuffle(self, rng=random):
        self._deck.extend(self._discard)
        self._discard.clear()
        rng.shuffle(self._deck)

    def deal(self):
        card = self._deck.pop()
        self._discard.append(card)
        return card

    def cut(self, depth=None, rng=random):
        depth = rng.randrange(len(self._deck)) if depth is None else int(depth)
        if depth > len(self._deck):
            raise ValueError()
        self._deck[:] = [*self._deck[depth:], *self._deck[:depth]]