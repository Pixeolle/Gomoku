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

    def __eq__(self, other : 'Board') -> bool:
        if isinstance(other, Board):
            return self.position == other.position and self.mask == other.mask
        return False

    def copy(self) -> 'Board':
        new_board = Board(self.height, self.width)
        new_board.position = self.position
        new_board.mask = self.mask
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

        if move not in self.can_play :
            raise ValueError(f"Position must be free : {move}")

        bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height
        self.mask |= (1 << bit_offset)
        if player == 1:
            self.position |= (1 << bit_offset)

        self.key = (self.mask << self.height * self.width ) | self.position
        return self

    def undo_to(self, move : str) -> 'Board':
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

    def invert_key(self) -> int:
        position = self.invert_one_zero(self.position) & self.mask
        key = (self.mask << self.height * self.width ) | position
        return key

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

    def forced_moves_fix(self, player : int, move : str) -> Optional[List[str]]:

        def valid_bit_by_offset(bit_offset : int, offset : int, k : int):
            if offset == 1 and bit_offset % self.height > self.height - k:
                return True
            elif offset == self.height and bit_offset // self.width > self.height - k:
                return True
            elif offset == self.height - 1 and (bit_offset // self.height > self.width - k or bit_offset % self.height < k - 1):
                return True
            elif offset == self.height + 1 and (bit_offset // self.height > self.width - k or bit_offset % self.height > self.height - k):
                return True
            return False

        def check_k_row(bitboard : int, opponent_bit : int, line_move : int, column_move, k : int) -> Optional[List[str]]:
            if k == 5:
                ones_need = 4
            elif k == 6:
                ones_need = 3
            else:
                raise ValueError (f"k must be 5 or 6 : {k}")

            if self.count_ones(bitboard) < ones_need:
                return

            offsets = [1, self.height, self.height - 1, self.height + 1]
            bit_offset_start = self.height - (line_move - k + 1) - 1 + (self.width - (column_move - k + 1) - 1) * self.height
            bit_offset_end = self.height - (line_move + k - 1) - 1 + (self.width - (column_move + k - 1) - 1) * self.height

            for offset in offsets:

                 bit_offset = bit_offset_start

                 while bit_offset < self.height * self.height and self.count_ones((bitboard >> bit_offset)) >= ones_need:
                     if self.count_ones((bitboard >> bit_offset) & self.mask_one[k][offset]) < ones_need or valid_bit_by_offset(bit_offset, offset, k):
                        bit_offset += 1
                        continue

                     selected_bit = Board.select_k_by_offset_bit((bitboard >> bit_offset), k, offset)
                     select_opponent = Board.select_k_by_offset_bit((opponent_bit >> bit_offset), k, offset)

                     if select_opponent != 0:
                         bit_offset += 1
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

        check_4_player = check_k_row(player_board, opponent_board, move, 5)
        if check_4_player is not None:
            return check_4_player

        check_4_opponent = check_k_row(opponent_board, player_board, move, 5)
        if check_4_opponent is not None:
            return check_4_opponent

        check_3_player = check_k_row(player_board, opponent_board, move, 6)
        if check_3_player is not None:
            return check_3_player

        check_3_opponent = check_k_row(opponent_board, player_board, move, 6)
        if check_3_opponent is not None:
            return check_3_opponent
        return None


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
        k = 5
        _, line_move, column_move = self.clean_move("h7")
        top = min(line_move + (k - 1) ,self.height)
        left = min(column_move + (k - 1) ,self.width)
        bottom = max(line_move - (k - 1) ,0)
        right = max(column_move - (k - 1) ,0)
        bit_offset_start = 10 #max(self.height - (line_move + (k - 1)) - 1 + (self.width - (column_move + (k - 1)) - 1) * self.height, 0)
        bit_offset_end = 225 #min(self.height - (line_move - (k - 1)) - 1 + (self.width - (column_move - (k - 1)) - 1) * self.height, self.height * self.width)


        print(f"{right} -> {left} ")
        print(f"{bottom} -> {top} ")

        str_to_print = ""
        for line in range(self.height):
            str_to_print += "   "
            str_to_print += "+"
            for column in range(self.width):
                str_to_print += "---+"
            str_to_print += f"\n {chr(ord('A') + line)} "

            for column in range(self.width):
                bit_offset = self.height - line - 1 + (self.width - column - 1) * self.height

                #str_to_print += f"| {bit_offset} "
                if column == column_move and line_move == line :
                    str_to_print += f"| \033[94mO\033[0m "
                elif left >= bit_offset // self.height >= right and  top >= bit_offset % self.height >= bottom : # rajouter la verification en fonction de la direction
                    str_to_print += f"| \033[91mX\033[0m "
                else:
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
