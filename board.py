import math
import random
import numpy as np
from typing import *


class Board:

    def __init__(self, height : int = 15, width : int = 15, pawn = 60):
        self.height : int = height
        self.width : int = width
        self.total_pawn = pawn * 2

        self.position : int = 0
        self.mask : int = 0
        self.bottom : int = 0

        self.bit_filter_1 = {
            1 : Board.bit_builder(height - 1, 1, width),
            height : Board.bit_builder(height * (width - 1)),
            height - 1 : Board.bit_builder(height - 1, 1, width - 1, False),
            height + 1 : Board.bit_builder(height - 1, 1, width - 1)
        }

        self.bit_filter_4 = {
            1 : Board.bit_builder(self.height - 4, 4, self.width),
            height : Board.bit_builder(self.height * (self.width - 4)),
            height - 1 : Board.bit_builder(self.height - 4, 4, self.width - 4, False),
            height + 1 : Board.bit_builder(self.height - 4, 4, self.width - 4)
        }

        self.key = (self.mask << self.height * self.width ) | self.position

    def __str__(self) -> str:
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

    def __eq__(self, other) -> bool:
        if isinstance(other, Board):
            return self.position == other.position and self.mask == other.mask
        return False

    def __hash__(self) -> int:
        return self.key

    def copy(self):
        new_board = Board(self.height, self.width)
        new_board.position = self.position
        new_board.mask = self.mask
        new_board.bottom = self.bottom
        new_board.key = self.key
        return new_board

    @property
    def remaining_moves(self) -> int:
        return self.total_pawn - Board.count_ones(self.mask)

    def clean_move(self, move : str) -> Tuple[str, int, int]:
        if len(move) < 2 or not move[1:].isdigit() or not move[0].isalpha():
            raise ValueError(f"Position must be a letter and a integer : {move}")

        move = move[0].upper() + move[1:]

        line = ord(move[0]) - ord("A")
        column = int(move[1:])

        if line < 0 or line > self.height - 1 or column < 0 or column > self.width - 1:
            raise ValueError(f"Position must be a letter between A and {chr(ord('A') + self.height - 1)} and a integer between 0 and {self.width - 1}")

        return move, line, column

    def distance(self, move_1, move_2) -> float:
        _, move_1_line, move_1_column = self.clean_move(move_1)
        _, move_2_line, move_2_column = self.clean_move(move_2)
        distance = max(abs(move_1_line - move_2_line), abs(move_1_column - move_2_column))
        return distance

    def get_left(self, number : int, position : int) -> int:
        if position < 0 or position >= self.height * self.width:
            raise ValueError(f"Position must be between 0 and {self.height * self.width - 1}")
        return (number >> (self.height * self.width - position - 1)) & 1

    def get_x_y(self,number : int, x : int, y : int ) -> int:
        if x < 0 or x >= self.height or y < 0 or y >= self.width:
            raise ValueError(f"X must be between 0 and {self.height - 1} Y must be between 0 and {self.width - 1}")
        return self.get_left(number, x + y * self.height)

    @property
    def can_play(self) -> List[str]:
        free_position = [self.bit_to_coordinate(bit) for bit in range(self.height * self.width) if (self.mask >> bit) & 1 == 0]
        return free_position

    def bit_to_coordinate(self, bit) -> str:
        if bit >= self.height * self.width:
            raise ValueError(f"Bit should be between 0 and {self.height * self.width - 1}")
        return chr(ord("A") + self.height - bit % self.height - 1) + str(self.width - bit // self.width - 1)

    def coordinate_to_bit(self, move : str) -> int:
        _, line, column = self.clean_move(move)
        return self.height - line - 1 + (self.width - column - 1) * self.height

    def play_to(self, player : int, move : str) -> 'Board':

        if player not in [1, 2]:
            raise ValueError("Player is not 1 or 2")

        move, line, column = self.clean_move(move)

        if move not in self.can_play :
            raise ValueError(f"Position must be free")

        bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height
        self.mask |= (1 << bit_offset)
        if player == 1:
            self.position |= (1 << bit_offset)

        self.key = (self.mask << self.height * self.width ) | self.position
        return self

    def undo_to(self, move : str):
        move, line, column = self.clean_move(move)

        if move in self.can_play :
            raise ValueError(f"Position is not already taken")

        bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height
        self.mask ^= (1 << bit_offset)
        if (self.position >> bit_offset) & 1 == 1:
            self.position ^= (1 << bit_offset)

        self.key = (self.mask << self.height * self.width ) | self.position
        return self

    def check_winner(self, bitboard : int) -> bool:

        def check_direction() -> bool:
            bit_offset = bitboard & (bitboard >> 2 * offset)
            bit_offset &= (bit_offset >> offset)
            if bit_offset & (bit_offset >> offset) & self.bit_filter_4[offset] != 0:
                return True
            return False


        offsets = [1, self.height, self.height - 1, self.height + 1]


        for offset in offsets:
            if check_direction():
                return True
        return False

    @staticmethod
    def count_ones(number: int) -> int:
        count = 0
        while number:
            number &= number - 1
            count += 1
        return count

    @property
    def is_winning(self) -> Optional[int]:

        if self.check_winner(self.position):
            return 1

        if self.check_winner(self.position ^ self.mask):
            return -1

        if Board.count_ones(self.mask) >= self.total_pawn:
            return 0

        return None

    @staticmethod
    def bit_builder(one : int, zero : int = 0, repeat : int = 1, start_one : bool = True) -> int:
        value = 0
        for i in range(repeat * (one + zero)):
            if start_one:
                if i % (one + zero) < one:
                    value |= (1 << i)
            else:
                if i % (one + zero) > zero - 1:
                    value |= (1<< i)

        return value

    def invert_one_zero(self, number : int) -> int:
        return ~number & ((1 << self.width * self.height) - 1)

    def find_1_to_k_near_position(self, k : int = - 1) -> List[Set[str]]:

        def get_k_near() -> Set[str]:
            k_near = set()

            offsets = [1, self.height, self.height - 1, self.height + 1]

            for offset in offsets:
                k_near |= get_k_near_by_direction(offset)

            return k_near

        def get_k_near_by_direction(offset : int) -> Set[str]:
            k_near = set()
            position_next_to_taken = mask ^ (mask >> offset)
            position_next_to_taken &= self.bit_filter_1[offset]

            for bit in range(self.height * self.width):
                if (position_next_to_taken >> bit) & 1 == 1:
                    if (mask >> bit) & 1 == 0:
                        k_near.add(self.bit_to_coordinate(bit))
                    else :
                        k_near.add(self.bit_to_coordinate(bit + offset))

            return k_near

        all_k_near = []
        mask = self.mask


        if k == - 1:
            while True :
                near = get_k_near()
                near = {x for x in near if not any(x in k_near for k_near in all_k_near)}
                if len(near) == 0:
                    return all_k_near
                all_k_near.append(near)
                for position in near:
                    mask |= (1 << self.coordinate_to_bit(position))


        for _ in range(1, k + 1):
            near = get_k_near()
            near = {x for x in near if not any(x in k_near for k_near in all_k_near)}
            all_k_near.append(near)
            for position in near:
                mask |= (1 << self.coordinate_to_bit(position))

        return all_k_near


