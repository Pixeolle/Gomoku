import math
from typing import *
from board import Board
from datetime import datetime, timedelta

class Solver:

    def __init__(self):
        self.table = {}

    def set(self, board : Board, value : int, position : str, depth : int, flag : str) -> None:
        self.table[hash(board)] = (value, position, depth, flag)

    def get(self, board) -> Tuple[int, str, int, str]:
        return self.table.get(hash(board))

    def solve(self, board: Board, player: int) -> str:
        offset = 0.01
        time_end : datetime = datetime.now() + timedelta(seconds= 5 - offset)

        depth = 0
        while datetime.now() < time_end:
            #best_move = self.alpha_beta(board, player, depth)
            depth += 1

        return "0"

    def alpha_beta(self, board : Board, player : int, depth : int, alpha : int = -float("inf"), beta : int = float("inf")):
        alpha_origin = alpha

        board_saved = self.get(board)

        if board_saved is not None and board_saved[1] >= depth:
            if board_saved[2] == "exact":
                return board_saved[0]
            elif board_saved[2] == "lowerbound":
                alpha = max(alpha, board_saved[0])
            elif board_saved[2] == "upperbound":
                beta = min(beta, board_saved[0])

            if alpha >= beta:
                return board_saved[0]

        if board.is_winning:
            return 61 * board.is_winning

        if depth == 0:
            return self.heuristic(board)

        child_boards = [board.copy().play_to(player, position) for position in board.can_play]
        child_boards.sort(key=lambda x : self.heuristic(x), reverse = (player == 1))

        value = -float("inf")
        next_player = 1 if player == 2 else 2

        for child_board in child_boards:
            value = max(value, -self.alpha_beta(child_board, next_player, depth - 1, -beta, -alpha))
            alpha = max(alpha, value)
            if alpha > beta:
                break

        if value <= alpha_origin:
            flag_to_save = "upperbound"
        elif value >= beta:
            flag_to_save = "lowerbound"
        else:
            flag_to_save = "exact"

        self.set(board, value, depth, flag_to_save)

        return value

    def heuristic(self, board, player : int) -> int:
        player_weights = {
            "4_open" : 10,
            "4_semi" : 6,
            "4_close" : 2,
            "3_open" : 5,
            "3_semi" : 3,
            "3_close" : 1,
            "2_open" : 3,
            "2_semi" : 2,
            "2_close" : 1
        }

        opponent_weights = {
            "4_open" : 10,
            "4_semi" : 6,
            "4_close" : 2,
            "3_open" : 5,
            "3_semi" : 3,
            "3_close" : 1,
            "2_open" : 3,
            "2_semi" : 2,
            "2_close" : 1
        }

        player_1 = self.get_k_row(board, player)
        player_2 = self.get_k_row(board, 1 if player == 2 else 2)

        #print(f"{sum(weight * player_1.get(key, 0) -  opponent_weights[key] * player_2.get(key, 0) for key, weight in player_weights.items())=}")
        return math.trunc(61 * sum(weight * player_1.get(key, 0) -  opponent_weights[key] * player_2.get(key, 0) for key, weight in player_weights.items()) / 100)

    def get_k_row(self, board, player) -> Dict[str, int]:
        count_k_row = {}
        ban_positions = {}

        for k in range(4, 1, - 1):
            positions = self.k_rows(board, player, k)
            valid_positions = {key: {value for value in positions if value not in ban_positions.get(Solver.get_key(key, alone = True), set())} for key, positions in positions.items()}

            for key, value in valid_positions.items():
                count_k_row[Solver.get_key(key, False)] = count_k_row.setdefault(Solver.get_key(key, False), 0) + len(value)

                ban_positions.setdefault(Solver.get_key(key, alone = True), set()).update(Solver.extend_ban_position(board, value, k, Solver.get_key(key, alone=True)))

        return count_k_row

    @staticmethod
    def k_rows(board : Board, player : int, k : int) -> Dict[str, Set[str]]:

        offset = k
        opponent_mask = board.invert_one_zero(board.position ^ board.mask) if player == 1 else board.invert_one_zero(board.position)
        bit_value = board.position if player == 1 else board.position ^ board.mask

        bit_vertical = bit_value
        bit_horizontal = bit_value
        bit_diagonalasc = bit_value
        bit_diagonaldesc = bit_value

        while offset > 1:
            bit_vertical &= (bit_vertical >> offset // 2)
            bit_horizontal &= (bit_horizontal >> (offset // 2) * board.height)
            bit_diagonalasc &= (bit_diagonalasc >> (offset // 2) * (board.height - 1))
            bit_diagonaldesc &= (bit_diagonaldesc >> (offset // 2) * (board.height + 1))

            offset -= offset //2

        vertical_filter = Board.bit_builder(board.height - k + 1, k - 1, board.width)
        horizontal_filter = Board.bit_builder(board.height * (board.width - k + 1), k - 1)
        diagonalasc_filter = Board.bit_builder(board.height - k + 1, k - 1, board.width - k + 1, False)
        diagonaldesc_filter = Board.bit_builder(board.height - k + 1, k - 1, board.width - k + 1)

        vertical = Solver.get_position_k_rows(board, bit_vertical, opponent_mask, k, 1, vertical_filter)
        horizontal = Solver.get_position_k_rows(board, bit_horizontal, opponent_mask, k, board.height, horizontal_filter)
        diagonalasc = Solver.get_position_k_rows(board, bit_diagonalasc, opponent_mask, k, board.height - 1, diagonalasc_filter)
        diagonaldesc = Solver.get_position_k_rows(board, bit_diagonaldesc, opponent_mask, k, board.height + 1, diagonaldesc_filter)

        k_rows = {f"{k}_{state}_{direction}": positions[i]
          for direction, positions in
                  zip(["vertical", "horizontal", "diagonalasc", "diagonaldesc"],
                      [vertical, horizontal, diagonalasc, diagonaldesc])
          for i, state in enumerate(["open", "semi", "close"])}

        return k_rows

    @staticmethod
    def get_position_k_rows(board, bit, opponent_mask, k, shift, bit_filter):
        mask_open = ((opponent_mask & (opponent_mask >> (k + 1) * shift )) << shift)
        mask_semi = ((opponent_mask ^ (opponent_mask >> (k + 1) * shift)) << shift)
        mask_close = board.invert_one_zero(((opponent_mask | (opponent_mask >> (k + 1) * shift)) << shift))

        open = bit & mask_open & bit_filter
        semi = bit & mask_semi & bit_filter
        close = bit & mask_close & bit_filter

        open_position = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (open >> bit) & 1 == 1}
        semi_position = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (semi >> bit) & 1 == 1}
        close_position = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (close >> bit) & 1 == 1}

        return open_position, semi_position, close_position

    @staticmethod
    def extend_ban_position(board : Board, positions : set, k : int, direction : str) -> Set[str]:
        banned_position = set(positions)
        for position in positions:
            match direction:
                case "vertical":
                    offset = 1
                case "horizontal":
                    offset = board.height
                case "diagonalasc":
                    offset = board.height - 1
                case "diagonaldesc":
                    offset = board.height + 1
                case _:
                    raise ValueError(f"The direction {direction} doesn't exist")

            for next_pawn in range(1, k):
                banned_position.add(board.bit_to_coordinate(board.coordinate_to_bit(position) + next_pawn * offset))

        return banned_position

    @staticmethod
    def get_key(key : str, direction : bool = True, alone : bool = False) -> str:
        if not alone :
            if direction :
                return key[:key.find("_")] + key[key.rfind("_"):]
            return key[:key.rfind("_")]
        if direction :
            return key[key.rfind("_") + 1:]
        return key[key.find("_") + 1: key.rfind("_")]

    @staticmethod
    def print_s(values : Set[str]) -> None:
        for value in values:
            print(f"{value} ", end="")
        print()