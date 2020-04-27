import collections
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
        self._data = list(
            map(
                Card,
                itertools.product(
                    Suit.__members__.values(), Value.__members__.values()
                ),
            )
        )
        if include_jokers:
            self._data.append(Card(joker=Joker.Red))
            self._data.append(Card(joker=Joker.Black))

    def draw(self, rng=random):
        return rng.choice(self._data)

