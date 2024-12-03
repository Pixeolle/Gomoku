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

    def heuristic(self, board) -> int:
        weights = {
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

        player_1 = self.get_k_row(board, 1)
        player_2 = self.get_k_row(board, 2)

        print(f"{sum(weight * (player_1.get(key, 0) - player_2.get(key, 0)) for key, weight in weights.items())=}")
        return math.trunc(61 * sum(weight * (player_1.get(key, 0) - player_2.get(key, 0)) for key, weight in weights.items()) / 100)

    def get_k_row(self, board, player) -> Dict[str, int]:
        count_k_row = {}
        ban_positions = {}

        for k in range(4, 1, - 1):
            positions = self.k_rows(board, player, k)
            valid_positions = {key : set(value not in ban_positions[Solver.get_key(key)]) for key, value in positions.items()}
            for key, value in valid_positions.items():
                count_k_row.setdefault(Solver.get_key(key, False), 0) + len(value)
                ban_positions.setdefault(Solver.get_key(key), set()).add(Solver.extend_ban_position(board, value, k, Solver.get_key(key, alone=True)))

        return count_k_row

    @staticmethod
    def k_rows(board : Board, player : int, k : int) -> Dict[str, Set[str]]:

        offset = k
        opponent_mask = board.invert_one_zero(board.position ^ board.mask) if player == 1 else board.invert_one_zero(board.position)

        bit_vertical = board.position if player == 1 else board.position ^ board.mask
        bit_horizontal = board.position if player == 1 else board.position ^ board.mask
        bit_diagonalasc = board.position if player == 1 else board.position ^ board.mask
        bit_diagonaldesc = board.position if player == 1 else board.position ^ board.mask

        while offset > 1:
            bit_vertical &= (bit_vertical >> offset // 2)
            bit_horizontal &= (bit_horizontal >> (offset // 2) * board.height)
            bit_diagonalasc &= (bit_diagonalasc >> (offset // 2) * (board.height - 1))
            bit_diagonaldesc &= (bit_diagonaldesc >> (offset // 2) * (board.height + 1))

            offset -= offset //2

        mask_open_vertical = ((opponent_mask & (opponent_mask >> k + 1)) << 1)
        mask_semi_vertical = ((opponent_mask ^ (opponent_mask >> k + 1)) << 1)
        mask_close_vertical = board.invert_one_zero(((opponent_mask | (opponent_mask >> k + 1)) << 1))

        mask_open_horizontal = ((opponent_mask & (opponent_mask >> (k + 1) * board.height)) << board.height)
        mask_semi_horizontal = ((opponent_mask ^ (opponent_mask >> (k + 1) * board.height)) << board.height)
        mask_close_horizontal = board.invert_one_zero(((opponent_mask | (opponent_mask >> (k + 1) * board.height)) << board.height))

        mask_open_diagonalasc = ((opponent_mask & (opponent_mask >> (k + 1) * (board.height - 1))) << board.height - 1)
        mask_semi_diagonalasc = ((opponent_mask ^ (opponent_mask >> (k + 1) * (board.height - 1))) << board.height - 1)
        mask_close_diagonalasc = board.invert_one_zero(((opponent_mask | (opponent_mask >> (k + 1) * (board.height - 1))) << board.height - 1))

        mask_open_diagonaldesc = ((opponent_mask & (opponent_mask >> (k + 1) * (board.height + 1))) << board.height + 1)
        mask_semi_diagonaldesc = ((opponent_mask ^ (opponent_mask >> (k + 1) * (board.height + 1))) << board.height + 1)
        mask_close_diagonaldesc = board.invert_one_zero(((opponent_mask | (opponent_mask >> (k + 1) * (board.height + 1))) << board.height + 1))

        vertical_filter = Board.bit_builder(board.height - k + 1, k - 1, board.width)
        horizontal_filter = Board.bit_builder(board.height * (board.width - k + 1), k - 1)
        diagonalasc_filter = Board.bit_builder(board.height - k + 1, k - 1, board.width - k + 1, False)
        diagonaldesc_filter = Board.bit_builder(board.height - k + 1, k - 1, board.width - k + 1)

        open_vertical = bit_vertical & mask_open_vertical & vertical_filter
        semi_vertical = bit_vertical & mask_semi_vertical & vertical_filter
        close_vertical = bit_vertical & mask_close_vertical & vertical_filter

        open_horizontal = bit_horizontal & mask_open_horizontal & horizontal_filter
        semi_horizontal = bit_horizontal & mask_semi_horizontal & horizontal_filter
        close_horizontal = bit_horizontal & mask_close_horizontal & horizontal_filter

        open_diagonalasc = bit_diagonalasc & mask_open_diagonalasc & diagonalasc_filter
        semi_diagonalasc = bit_diagonalasc & mask_semi_diagonalasc & diagonalasc_filter
        close_diagonalasc = bit_diagonalasc & mask_close_diagonalasc & diagonalasc_filter

        open_diagonaldesc = bit_diagonaldesc & mask_open_diagonaldesc & diagonaldesc_filter
        semi_diagonaldesc = bit_diagonaldesc & mask_semi_diagonaldesc & diagonaldesc_filter
        close_diagonaldesc = bit_diagonaldesc & mask_close_diagonaldesc & diagonaldesc_filter
        

        open_vertical_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (open_vertical >> bit) & 1 == 1}
        semi_vertical_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (semi_vertical >> bit) & 1 == 1}
        close_vertical_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (close_vertical >> bit) & 1 == 1}

        open_horizontal_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (open_horizontal >> bit) & 1 == 1}
        semi_horizontal_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (semi_horizontal >> bit) & 1 == 1}
        close_horizontal_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (close_horizontal >> bit) & 1 == 1}

        open_diagonalasc_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (open_diagonalasc >> bit) & 1 == 1}
        semi_diagonalasc_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (semi_diagonalasc >> bit) & 1 == 1}
        close_diagonalasc_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (close_diagonalasc >> bit) & 1 == 1}

        open_diagonaldesc_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (open_diagonaldesc >> bit) & 1 == 1}
        semi_diagonaldesc_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (semi_diagonaldesc >> bit) & 1 == 1}
        close_diagonaldesc_positions = {board.bit_to_coordinate(bit) for bit in range(board.height * board.width) if (close_diagonaldesc >> bit) & 1 == 1}

        k_rows = {
            f"{k}_open_vertical" : open_vertical_positions,
            f"{k}_semi_vertical" : semi_vertical_positions,
            f"{k}_close_vertical" : close_vertical_positions,
            f"{k}_open_horizontal" : open_horizontal_positions,
            f"{k}_semi_horizontal" : semi_horizontal_positions,
            f"{k}_close_horizontal" : close_horizontal_positions,
            f"{k}_open_diagonalasc" : open_diagonalasc_positions,
            f"{k}_semi_diagonalasc" : semi_diagonalasc_positions,
            f"{k}_close_diagonalasc" : close_diagonalasc_positions,
            f"{k}_open_diagonaldesc" : open_diagonaldesc_positions,
            f"{k}_semi_diagonaldesc" : semi_diagonaldesc_positions,
            f"{k}_close_diagonaldesc" : close_diagonaldesc_positions
        }

        return k_rows

    @staticmethod
    def extend_ban_position(board : Board, positions : set, k : int, direction : str) -> Set[str]:
        banned_position = set(positions)
        for position in positions:
            print(f"{position=}")
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