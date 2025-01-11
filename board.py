import math
import random
import shutil
from datetime import datetime

import numpy as np
from typing import *


class Board:

    def __init__(self, height : int = 15, width : int = 15, rule = "normal", pawn = 60):
        self.height : int = height
        self.width : int = width
        self.total_pawn = pawn * 2
        self.pawn_played = 0
        self.rule = rule

        self.position : int = 0
        self.mask : int = 0
        self.forced_bit_offset = {
            "4_p1" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "4_p2" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "3_p1" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "3_p2" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            }
        }

        self.heuristic_value = 0
        self.alignment_bit_offset = {
            "4_p1" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "4_p2" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "3_p1" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "3_p2" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "2_p1" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
            "2_p2" : {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            },
        }

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

        self.mask_one = {
            5 : {
                1 : Board.bit_builder(5),
                self.height : Board.bit_builder(1, self.height - 1, 5),
                self.height - 1 : Board.bit_builder(1, self.height - 2, 5),
                self.height + 1 : Board.bit_builder(1, self.height , 5)
            },

            6 : {
                1 : Board.bit_builder(6),
                self.height : Board.bit_builder(1, self.height - 1, 6),
                self.height - 1 : Board.bit_builder(1, self.height - 2, 6),
                self.height + 1 : Board.bit_builder(1, self.height , 6)
            }
        }

        self.key = 0

    def __str__(self) -> str:
        number_to_object = {0: "\033[91mX\033[0m", 1: "\033[94mO\033[0m"}
        terminal_width = shutil.get_terminal_size().columns
        board_width = self.width * 4 + 3
        padding = " " * ((terminal_width - board_width) // 2)
        str_to_print = ""

        str_to_print += f"{padding}    "
        for column in range(self.width):
            str_to_print += f" {column:<2} "
        str_to_print += "\n"

        for line in range(self.height):
            str_to_print += f"{padding}   +"
            for column in range(self.width):
                str_to_print += "---+"
            str_to_print += f"\n{padding} {chr(ord('A') + line)} "

            for column in range(self.width):
                bit_mask = self.get_left(self.mask, self.height * column + line)
                if bit_mask == 0:
                    str_to_print += "|   "
                else:
                    bit_position = self.get_left(self.position, self.height * column + line)
                    str_to_print += f"| {number_to_object[bit_position]} "
            str_to_print += f"| {chr(ord('A') + line)}\n"

        str_to_print += f"{padding}   +"
        for column in range(self.width):
            str_to_print += "---+"
        str_to_print += f"\n{padding}    "
        for column in range(self.width):
            str_to_print += f" {column:<2} "
        str_to_print += "\n"

        return str_to_print

    def __eq__(self, other : 'Board') -> bool:
        if isinstance(other, Board):
            return self.position == other.position and self.mask == other.mask
        return False

    def copy(self) -> 'Board':
        new_board = Board(self.height, self.width)
        new_board.total_pawn = self.total_pawn
        new_board.pawn_played = self.pawn_played
        new_board.rule = self.rule

        new_board.position = self.position
        new_board.mask = self.mask
        new_board.forced_bit_offset = self.forced_bit_offset

        new_board.heuristic_value = self.heuristic_value
        new_board.alignment_bit_offset = self.alignment_bit_offset

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

    def distance(self, move_1 : str, move_2 : str) -> float:
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
        if self.rule == "long pro":
            if self.pawn_played == 0:
                return ["H7"]
            if self.pawn_played == 2:
                free_position = []

                middle_height = self.height // 2
                middle_width = self.width // 2
                for bit_offset in range(self.height * self.width):
                    line = bit_offset % self.height
                    column = bit_offset // self.height
                    if not (middle_height - 3 <= line <= middle_height + 3 and middle_width - 3 <= column <= middle_width + 3):
                        free_position.append(self.bit_to_coordinate(bit_offset))

                return free_position

        free_position = [self.bit_to_coordinate(bit) for bit in range(self.height * self.width) if (self.mask >> bit) & 1 == 0]

        return free_position

    def bit_to_coordinate(self, bit : int, bit_offset = -1) -> str:
        if bit >= self.height * self.width:
            raise ValueError(f"Bit should be between 0 and {self.height * self.width - 1} : {bit} : {bit_offset}")
        return chr(ord("A") + self.height - bit % self.height - 1) + str(self.width - bit // self.width - 1)

    def coordinate_to_bit(self, move : str) -> int:
        _, line, column = self.clean_move(move)
        return self.height - line - 1 + (self.width - column - 1) * self.height

    def play_to(self, player : int, move : str) -> 'Board':

        if player not in [1, 2]:
            raise ValueError(f"Player is not 1 or 2 : {player}")

        move, line, column = self.clean_move(move)

        if self.rule == "long pro" and self.pawn_played in [0, 2] and move not in self.can_play:
            raise ValueError(f"Position not allow by {self.rule} rules : {move}")

        bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height
        if (self.mask >> bit_offset) & 1 == 1:
            raise ValueError(f"Position must be free : {move}")

        self.mask |= (1 << bit_offset)
        if player == 1:
            self.position |= (1 << bit_offset)

        self.pawn_played += 1

        self.update_forced_moves(player, bit_offset)
        self.update_alignment(player, bit_offset)

        return self

    def undo_to(self, move : str, player : int) -> 'Board':
        move, line, column = self.clean_move(move)

        if move in self.can_play :
            raise ValueError(f"Position is not already taken")

        if player not in [1, 2]:
            raise ValueError(f"Player is not 1 or 2 : {player}")

        bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height

        bitboard = self.position if player == 1 else self.position ^ self.mask
        if (bitboard >> bit_offset) & 1 != 1:
            raise ValueError(f"This position is not taken by player {player}")

        self.mask ^= (1 << bit_offset)
        if (self.position >> bit_offset) & 1 == 1:
            self.position ^= (1 << bit_offset)

        self.pawn_played -= 1

        self.update_forced_moves(player, bit_offset)

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

        if self.pawn_played >= self.total_pawn:
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

    def rotated_key(self) -> List[int]:
        def rotated_bit(bitboard : int) -> int:
            rotated = 0
            for row in range(self.height):
                for col in range(self.width):
                    if (bitboard >> (row * self.width + col)) & 1:
                        rotated |= 1 << (col * self.height + (self.height - row - 1))
            return rotated

        position = self.position
        mask = self.mask
        keys = [self.key]

        for _ in range(3):
            mask = rotated_bit(mask)
            position = rotated_bit(position)
            keys.append((mask << self.height * self.width ) | position)

        return keys

    def turn_move(self, move : str, angle : int = 0):
        middle_line = (self.height - 1) // 2
        middle_column = (self.width - 1) // 2
        _, line, column = self.clean_move(move)

        match angle:
            case 0 :
                return move
            case 1 :
                return chr(ord('A') + middle_line - column + middle_column) + str(middle_column - middle_line + line)
            case 2 :
                return chr(ord('A') + 2 * middle_line - line) + str(2 * middle_column - column)
            case 3 :
                return chr(ord('A') + middle_line + column - middle_column) + str(middle_column + middle_line - line)
            case _ :
                raise ValueError(f"Angle is not valid : {angle}")

    @staticmethod
    def select_k_by_offset_bit(bitboard : int, k : int, offset : int) -> int:
        index = 1
        result = bitboard & 1
        while bitboard != 0 and index < k:
            bitboard >>= offset
            result |= ((bitboard & 1) << index)
            index += 1

        return result

    def forced_moves(self, player : int) -> Optional[List[str]]:

        def check_k_row(bitboard : int, opponent_bit : int, k : int) -> Optional[List[str]]:
            if k == 5:
                ones_need = 4
            elif k == 6:
                ones_need = 3
            else:
                raise ValueError (f"k must be 5 or 6 : {k}")

            if self.count_ones(bitboard) < ones_need:
                return

            offsets = [1, self.height, self.height - 1, self.height + 1]
            bit_offset = 0
            ones_mask = (1 << (self.height + 1) * (k - 1) + 1) - 1
            while bit_offset < self.height * self.height and self.count_ones((bitboard >> bit_offset)) >= ones_need: # Ajouter une contrainte pour éviter les zones vides avant la zone interessante

                if self.count_ones((bitboard >> bit_offset) & ones_mask) < ones_need:
                    bit_offset += 1
                    continue

                for offset in offsets:

                    if offset == 1 and bit_offset % self.height > self.height - k:
                        continue
                    elif offset == self.height and bit_offset // self.width > self.height - k:
                        continue
                    elif offset == self.height - 1 and (bit_offset // self.height > self.width - k or bit_offset % self.height < k - 1):
                        continue
                    elif offset == self.height + 1 and (bit_offset // self.height > self.width - k or bit_offset % self.height > self.height - k):
                        continue

                    selected_bit = Board.select_k_by_offset_bit((bitboard >> bit_offset), k, offset)
                    select_opponent = Board.select_k_by_offset_bit((opponent_bit >> bit_offset), k, offset)

                    if select_opponent != 0:
                        continue

                    if k == 5:
                        match selected_bit:
                            case 0b01111:
                                return [self.bit_to_coordinate(bit_offset + 4 * offset)]
                            case 0b10111:
                                return [self.bit_to_coordinate(bit_offset + 3 * offset)]
                            case 0b11011:
                                return [self.bit_to_coordinate(bit_offset + 2 * offset)]
                            case 0b11101:
                                return [self.bit_to_coordinate(bit_offset + 1 * offset)]
                            case 0b11110:
                                return [self.bit_to_coordinate(bit_offset)]
                    elif k == 6:
                        match selected_bit:
                            case 0b001110:
                                return [self.bit_to_coordinate(bit_offset + 4 * offset), self.bit_to_coordinate(bit_offset)]
                            case 0b010110:
                                return [self.bit_to_coordinate(bit_offset + 3 * offset), self.bit_to_coordinate(bit_offset), self.bit_to_coordinate(bit_offset + 5 * offset, bit_offset)]
                            case 0b011010:
                                return [self.bit_to_coordinate(bit_offset + 2 * offset), self.bit_to_coordinate(bit_offset), self.bit_to_coordinate(bit_offset + 5 * offset, bit_offset)]
                            case 0b011100:
                                return [self.bit_to_coordinate(bit_offset + 1 * offset), self.bit_to_coordinate(bit_offset + 5 * offset)]

                bit_offset += 1

        player_board = self.position if player == 1 else self.position ^ self.mask
        opponent_board = self.position if player == 2 else self.position ^ self.mask

        check_4_player = check_k_row(player_board, opponent_board, 5)
        if check_4_player is not None:
            return check_4_player
        check_4_opponent = check_k_row(opponent_board, player_board, 5)
        if check_4_opponent is not None:
            return check_4_opponent
        check_3_player = check_k_row(player_board, opponent_board, 6)
        if check_3_player is not None:
            return check_3_player
        check_3_opponent = check_k_row(opponent_board, player_board,6)
        if check_3_opponent is not None:
            return check_3_opponent
        return None

    def forced_moves_opti(self, player : int) -> Optional[Set]:

        def check_bit_offset_saved(type_search : str, player_board : int, opponent_board : int, k) -> Optional[Set]:

            bit_offset_by_direction = self.forced_bit_offset[type_search]
            discard, check = check_k_row(player_board, opponent_board, bit_offset_by_direction, k)

            for key, value in discard.items():
                self.forced_bit_offset[type_search][key].difference_update(value)

            return check if len(check) > 0 else None

        def check_k_row(bitboard : int, opponent_bit : int, bit_offset_by_direction : Dict[int, Set[int]], k : int) -> Tuple[Dict[int, Set[int]], Set[str]]:
            if k == 5:
                ones_need = 4
            elif k == 6:
                ones_need = 3
            else:
                raise ValueError (f"k must be 5 or 6 : {k}")

            if self.count_ones(bitboard) < ones_need:
                return bit_offset_by_direction, set()

            offsets = [1, self.height, self.height - 1, self.height + 1]
            bit_offset_to_discard = {
                1 : set(),
                self.height : set(),
                self.height - 1 : set(),
                self.height + 1 : set()
            }

            for offset in offsets:

                current_offset_bits = bit_offset_by_direction[offset]

                for bit_offset in current_offset_bits:

                    if self.count_ones((bitboard >> bit_offset) & self.mask_one[k][offset]) < ones_need:
                        bit_offset_to_discard[offset].add(bit_offset)
                        continue

                    selected_bit = Board.select_k_by_offset_bit((bitboard >> bit_offset), k, offset)
                    select_opponent = Board.select_k_by_offset_bit((opponent_bit >> bit_offset), k, offset)

                    if select_opponent != 0:
                        bit_offset_to_discard[offset].add(bit_offset)
                        continue

                    if k == 5:
                        match selected_bit:
                            case 0b01111:
                                return bit_offset_to_discard, {self.bit_to_coordinate(bit_offset + 4 * offset)}
                            case 0b10111:
                                return bit_offset_to_discard, {self.bit_to_coordinate(bit_offset + 3 * offset)}
                            case 0b11011:
                                return bit_offset_to_discard, {self.bit_to_coordinate(bit_offset + 2 * offset)}
                            case 0b11101:
                                return bit_offset_to_discard, {self.bit_to_coordinate(bit_offset + 1 * offset)}
                            case 0b11110:
                                return bit_offset_to_discard, {self.bit_to_coordinate(bit_offset)}
                    elif k == 6:
                        match selected_bit:
                            case 0b001110:
                                return bit_offset_to_discard, {self.bit_to_coordinate(bit_offset + 4 * offset), self.bit_to_coordinate(bit_offset)}
                            case 0b010110:
                                return bit_offset_to_discard,{self.bit_to_coordinate(bit_offset + 3 * offset), self.bit_to_coordinate(bit_offset), self.bit_to_coordinate(bit_offset + 5 * offset, bit_offset)}
                            case 0b011010:
                                return bit_offset_to_discard,{self.bit_to_coordinate(bit_offset + 2 * offset), self.bit_to_coordinate(bit_offset), self.bit_to_coordinate(bit_offset + 5 * offset, bit_offset)}
                            case 0b011100:
                                return bit_offset_to_discard,{self.bit_to_coordinate(bit_offset + 1 * offset), self.bit_to_coordinate(bit_offset + 5 * offset)}

                    bit_offset_to_discard[offset].add(bit_offset)

            return bit_offset_to_discard, set()

        player_board = self.position if player == 1 else self.position ^ self.mask
        opponent_board = self.position if player == 2 else self.position ^ self.mask
        opponent = player ^ 3

        k = 5
        check_4_player = check_bit_offset_saved(f"4_p{player}", player_board, opponent_board, k)
        if check_4_player is not None:
            return check_4_player

        check_4_opponent = check_bit_offset_saved(f"4_p{opponent}", opponent_board, player_board, k)
        if check_4_opponent is not None:
            return check_4_opponent

        k = 6
        check_3_player = check_bit_offset_saved(f"3_p{player}", player_board, opponent_board, k)
        if check_3_player is not None:
            return check_3_player

        check_3_opponent = check_bit_offset_saved(f"3_p{opponent}", opponent_board, player_board, k)
        if check_3_opponent is not None:
            return check_3_opponent

        return None

    def generate_bit_offset(self, origin_offset, offset, k):
        def valid_bit_offset_by_direction(bit_offset, offset, k):
            if bit_offset < 0:
                return False
            elif (offset == 1 or offset == self.height + 1) and bit_offset % self.height > self.height - k:
                return False
            elif (offset == self.height or offset == self.height - 1 or offset == self.height + 1) and bit_offset // self.height > self.width - k:
                return False
            elif offset == self.height - 1 and bit_offset % self.height < k - 1:
                return False
            return True

        bits = set()
        start = 0 if k == 5 else 1

        for index in range(start, 5):
            bit_to_append = origin_offset - index * offset
            if valid_bit_offset_by_direction(bit_to_append, offset, k) :
                bits.add(bit_to_append)

        return bits

    def update_forced_moves(self, player : int, bit_offset_point : int):

        def check_k_row_by_bit_offset(bitboard : int, opponent_bit : int, bit_offset, offset : int, k : int) -> Optional[Set[str]]:
            if k == 5:
                ones_need = 4
            elif k == 6:
                ones_need = 3
            else:
                raise ValueError (f"k must be 5 or 6 : {k}")

            if self.count_ones(bitboard) < ones_need:
                return

            if self.count_ones((bitboard >> bit_offset) & self.mask_one[k][offset]) < ones_need:
                return

            selected_bit = Board.select_k_by_offset_bit((bitboard >> bit_offset), k, offset)
            select_opponent = Board.select_k_by_offset_bit((opponent_bit >> bit_offset), k, offset)

            if select_opponent != 0:
                return

            if k == 5:
                match selected_bit:
                    case 0b01111:
                        return {self.bit_to_coordinate(bit_offset + 4 * offset)}
                    case 0b10111:
                        return {self.bit_to_coordinate(bit_offset + 3 * offset)}
                    case 0b11011:
                        return {self.bit_to_coordinate(bit_offset + 2 * offset)}
                    case 0b11101:
                        return {self.bit_to_coordinate(bit_offset + 1 * offset)}
                    case 0b11110:
                        return {self.bit_to_coordinate(bit_offset)}
            elif k == 6:
                match selected_bit:
                    case 0b001110:
                        return {self.bit_to_coordinate(bit_offset + 4 * offset), self.bit_to_coordinate(bit_offset)}
                    case 0b010110:
                        return {self.bit_to_coordinate(bit_offset + 3 * offset), self.bit_to_coordinate(bit_offset), self.bit_to_coordinate(bit_offset + 5 * offset, bit_offset)}
                    case 0b011010:
                        return {self.bit_to_coordinate(bit_offset + 2 * offset), self.bit_to_coordinate(bit_offset), self.bit_to_coordinate(bit_offset + 5 * offset, bit_offset)}
                    case 0b011100:
                        return {self.bit_to_coordinate(bit_offset + 1 * offset), self.bit_to_coordinate(bit_offset + 5 * offset)}

            return

        player_board = self.position if player == 1 else self.position ^ self.mask
        opponent_board = self.position if player == 2 else self.position ^ self.mask
        offsets = [1, self.height, self.height - 1, self.height + 1]


        k = 5
        for offset in offsets:
            bit_offset_by_direction = self.generate_bit_offset(bit_offset_point, offset, k)
            for bit_offset in bit_offset_by_direction:
                result = check_k_row_by_bit_offset(player_board, opponent_board, bit_offset, offset, k)
                if result is None:
                    self.forced_bit_offset[f"4_p{player}"][offset].discard(bit_offset)
                else:
                    self.forced_bit_offset[f"4_p{player}"][offset].add(bit_offset)

        k = 6
        for offset in offsets:
            bit_offset_by_direction = self.generate_bit_offset(bit_offset_point, offset, k)
            for bit_offset in bit_offset_by_direction:
                result = check_k_row_by_bit_offset(player_board, opponent_board, bit_offset, offset, k)

                if result is None:
                    self.forced_bit_offset[f"3_p{player}"][offset].discard(bit_offset)
                else :
                    self.forced_bit_offset[f"3_p{player}"][offset].add(bit_offset)

    def update_alignment(self, player : int, bit_offset_point : int, ghost : bool = False):

        def check_alignment(bitboard : int, opponent_bit : int, bit_offset : int, offset : int, k : int):
            selected_bit = Board.select_k_by_offset_bit((bitboard >> bit_offset), k, offset)
            select_opponent = Board.select_k_by_offset_bit((opponent_bit >> bit_offset), k, offset)

            if select_opponent != 0:
                return None

            stone_find = self.count_ones(selected_bit)
            if stone_find < 2:
                return None

            return stone_find

        weight = {
            2 : 40,
            3 : 75,
            4 : 140,
            5 : 10000
        }

        player_board = self.position if player == 1 else self.position ^ self.mask
        opponent_board = self.position if player == 2 else self.position ^ self.mask

        if ghost :
            player_board |= (1 << bit_offset_point)

        offsets = [1, self.height, self.height - 1, self.height + 1]
        opponent = player ^ 3
        update_value = 0

        for offset in offsets:
            bit_offset_by_direction = self.generate_bit_offset(bit_offset_point, offset, 5)
            for bit_offset in bit_offset_by_direction:
                result_player = check_alignment(player_board, opponent_board, bit_offset, offset, 5)
                if result_player is not None:
                    if result_player < 5 and not ghost:
                        self.alignment_bit_offset[f"{result_player}_p{player}"][offset].add(bit_offset)
                    update_value += weight[result_player]

                for alignement_range in range(2, 5):
                    if bit_offset in self.alignment_bit_offset[f"{alignement_range}_p{opponent}"][offset]:
                        result_opponent = check_alignment(opponent_board, player_board, bit_offset, offset, 5)
                        if result_opponent is None :
                            if not ghost:
                                self.alignment_bit_offset[f"{alignement_range}_p{opponent}"][offset].discard(bit_offset)
                            update_value += weight[alignement_range]

        if ghost :
            return update_value

        relative_value = update_value if player == 1 else -update_value
        self.heuristic_value += relative_value

    def heuristic(self, value : int, move : str, player : int, display = False) -> int:

        def heuristic_direction(bit_shift, offset : int, player_bits : int, opponent_bits : int) -> int:


            attack_sum = 0
            attack_max = 0
            defense_sum = 0
            defense_max = 0

            weight = {
                2 : 10,
                3 : 100,
                4 : 150,
                5 : 10000
            }

            for i in range(5):
                total_offset = bit_shift - i * offset
                if total_offset < 0:
                    break

                player_selection = self.select_k_by_offset_bit((player_bits >> total_offset), 5, offset)
                opponent_selection = self.select_k_by_offset_bit((opponent_bits >> total_offset), 5, offset)

                if self.count_ones(opponent_selection) == 0:
                    player_stone = self.count_ones(player_selection)
                    if player_stone > 1:
                        if player_stone > attack_max:
                            attack_max = player_stone

            if attack_max > 1 and display :
                print("Alignement trouvé")

            for i in range(attack_max, 1, -1):
                attack_sum += weight.get(i, 0)

            tot_sum = attack_sum - defense_sum if player == 1 else defense_sum - attack_sum
            return tot_sum

        value_direction = 0

        player_bits = self.position if player == 1 else self.position ^ self.mask
        opponent_bits = self.position if player == 2 else self.position ^ self.mask
        bit_shift = self.coordinate_to_bit(move)
        player_bits |= (1 << bit_shift)

        if display :
            print(f"Move : {move}")

        offsets = [1, self.height, self.height - 1, self.height + 1]

        for offset in offsets:
            value_direction += heuristic_direction(bit_shift, offset, player_bits, opponent_bits)

        if display :
            print(f"Value to add : {value_direction} \n")
        return value + value_direction

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

    def get_distance(self) -> str:
        number_to_object = {0: "\033[91mX\033[0m", 1: "\033[94mO\033[0m"}
        distance_to_object = {
            1: "\033[91m1\033[0m",  # Red
            2: "\033[93m2\033[0m",  # Yellow
            3: "\033[92m3\033[0m",  # Green
            4: "\033[96m4\033[0m",  # Cyan
            5: "\033[94m5\033[0m",  # Blue
            6: "\033[95m6\033[0m",  # Magenta
            7: "\033[97m7\033[0m"   # White
        }
        distances = self.find_1_to_k_near_position()
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
                    bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height
                    move = self.bit_to_coordinate(bit_offset)
                    rank = - 1
                    for index, k_distance in enumerate(distances, 1):
                        if move in k_distance:
                            rank = index
                            break

                    str_to_print += f"| {distance_to_object.get(rank, 7)} "
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

    def get_test(self):

        def valid_bit_offset_by_direction(bit_offset, offset, k):
            if bit_offset < 0:
                return False
            elif (offset == 1 or offset == self.height + 1) and bit_offset % self.height > self.height - k:
                return False
            elif (offset == self.height or offset == self.height - 1 or offset == self.height + 1) and bit_offset // self.height > self.width - k:
                return False
            elif offset == self.height - 1 and bit_offset % self.height < k - 1:
                return False
            return True

        def generate_bit_offset(origin_offset, offset):
            bits = []

            for index in range(1, 5):
                bit_to_append = origin_offset - index * offset
                if valid_bit_offset_by_direction(bit_to_append, offset, 5) :
                    bits.append(bit_to_append)

            return bits

        move = "C2"
        offsets = [1, self.height, self.height - 1, self.height + 1]
        distance_to_object = {
            offsets[0] : "\033[92mX\033[0m",  # Green
            offsets[1] : "\033[96mX\033[0m",  # Cyan
            offsets[2] : "\033[91mX\033[0m",  # Blue
            offsets[3] : "\033[95mX\033[0m",  # Magenta
        }

        _, line_move, column_move = self.clean_move(move)
        bit_offset_point = self.coordinate_to_bit(move)
        bit_offset_by_direction = {offset : generate_bit_offset(bit_offset_point, offset) for offset in offsets}
        print(f"{bit_offset_by_direction}")


        str_to_print = ""
        for line in range(self.height):
            str_to_print += "   "
            str_to_print += "+"
            for column in range(self.width):
                str_to_print += "---+"
            str_to_print += f"\n {chr(ord('A') + line)} "

            for column in range(self.width):
                bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height

                #str_to_print += f"| {bit_offset % self.height} "


                if bit_offset == bit_offset_point  :
                    str_to_print += f"| \033[94mO\033[0m "
                else:
                    find = False
                    for offset in offsets :
                        if bit_offset in bit_offset_by_direction[offset] and not find:
                            str_to_print += f"| {distance_to_object[offset]} "
                            find = True
                    if not find:
                        str_to_print += f"|   "


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
