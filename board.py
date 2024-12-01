import random

import numpy as np
from typing import Optional


class Board:

    def __init__(self, height = 5, width = 5):
        self.height : int = height
        self.width : int = width
        required_bits : int = height * width

        self.min_exact : Optional[int] = None
        self.max_exact : Optional[int] = None
        self.min : Optional[int] = None
        self.max : Optional[int] = None
        self.position_min : Optional[int] = None
        self.position_max : Optional[int] = None

        self.position : int = 0
        self.mask : int = 0
        self.bottom : int = 0

        self.key = (self.mask << required_bits ) | self.position


    def __str__(self):
        number_to_object = {0: "\033[91mX\033[0m", 1: "\033[94mO\033[0m"}
        str_to_print : str = ""

        for line in range(self.height):
            str_to_print += "   "
            str_to_print += "+"
            for column in range(self.width):
                str_to_print += "---+"
            str_to_print += f"\n {chr(ord('A') + line)} "

            for column in range(self.width):
                bit_mask = self.get_left(self.mask, self.height * column + line)
                if bit_mask == 0:
                    str_to_print += f"|   "
                else:
                    bit_position = self.get_left(self.position, self.height * column + line)
                    str_to_print += f"| {number_to_object[bit_position]} "
            str_to_print += "|\n"

        str_to_print += "   "
        str_to_print += "+"
        for column in range(self.width):
            str_to_print += "---+"
        str_to_print += "\n"
        str_to_print += "    "
        for column in range(self.width):
            str_to_print += f" {column:<2} "
        str_to_print += "\n"

        return str_to_print


    def __hash__(self):
        return self.key

    def get_left(self, number, position):
        if position < 0 or position >= self.height * self.width:
            raise ValueError(f"Position must be between 0 and {self.height * self.width - 1}")
        return (number >> (self.height * self.width - position - 1)) & 1

    def get_x_y(self,number, x, y ):
        if x < 0 or x >= self.height or y < 0 or y >= self.width:
            raise ValueError(f"X must be between 0 and {self.height - 1} Y must be between 0 and {self.width - 1}")
        return self.get_left(number, x + y * self.height)

    @property
    def can_play(self):
        free_position = [chr(ord("A") + self.height - bit % self.width - 1) + str( self.width - bit // self.width - 1) for bit in range(self.height * self.width) if (self.mask >> bit) & 1 == 0]
        return free_position

    def play_to(self, player, position : str): # A fixer indice pas bon
        if len(position) != 2 or not position[1].isdigit() or not position[0].isalpha():
            raise ValueError(f"Position must be a letter and a integer")

        if player not in [1, 2]:
            raise ValueError("Player is not 1 or 2")

        position = position[0].upper() + position[1]

        line = ord(position[0]) - ord("A")
        column = int(position[1])

        if line < 0 or line > self.height - 1 or column < 0 or column > self.width - 1:
            raise ValueError(f"Position must be a letter between A and {chr(ord('A') + self.height - 1)} and a integer between 0 and {self.width - 1}")

        if position not in self.can_play :
            raise ValueError(f"Position must be free")

        bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height
        self.mask |= (1 << bit_offset)
        if player == 1:
            self.position |= (1 << bit_offset)



board = Board()
print(board)

a = None
player = random.randint(1, 2)
while a != "stop":

    try:
        print(f"Player {player} turn")
        a = input()
        board.play_to(player, a)

    except ValueError as e:
        print(f"Error : {e}")

    player = 1 if player == 2 else 2
    print(board)
    print(board.can_play)
