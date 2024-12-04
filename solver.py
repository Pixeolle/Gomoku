import math
from typing import *
from board import Board
from datetime import datetime, timedelta

class Solver:

    def __init__(self, timeout = 5, offset = 0.01):
        self.table = {}
        self.timeout = timeout
        self.offset = offset

    def set(self, board : Board, position : str,  value : int, depth : int, flag : str) -> None:
        self.table[hash(board)] = (position, value, depth, flag)

    def get(self, board) -> Tuple[str, int, int, str]:
        return self.table.get(hash(board))

    def solve(self, board: Board, player: int) -> str:
        offset = 0.01
        time_end : datetime = datetime.now() + timedelta(seconds= self.timeout - self.offset)

        depth = 1
        while datetime.now() < time_end and depth <= board.remaining_moves:
            best_move, value = self.alpha_beta(board, player, depth, time_end)
            print(f"Profondeur = {depth}, Mouvement = {best_move}, Valeur = {value}")
            depth += 1

        return best_move

    def alpha_beta(self, board : Board, player : int, depth : int, time_end : datetime, alpha : int = -float("inf"), beta : int = float("inf")) -> Tuple[Optional[str], int]:
        alpha_origin = alpha
        board_saved = self.get(board)


        #print("Board")
        if board_saved is not None and board_saved[2] >= depth:
            #print("Saved")
            if board_saved[2] == "exact":
                return board_saved[0], board_saved[1]
            elif board_saved[2] == "lowerbound":
                alpha = max(alpha, board_saved[1])
            elif board_saved[2] == "upperbound":
                beta = min(beta, board_saved[1])

            if alpha >= beta:
                return board_saved[0], board_saved[1]

        if board.is_winning:
            #print("Terminal")
            return None, 61 * board.is_winning

        if depth == 0 or datetime.now() >= time_end:
            return None, self.heuristic(board, player)

        child_boards = [(board.copy().play_to(player, position), position) for position in board.can_play]
        child_boards.sort(key=lambda x : (self.heuristic(x[0], player), board.distance(x[1])), reverse = (player == 1))
        if len(child_boards) > 60:
            child_boards = child_boards[:60]

        value = -float("inf") if player == 1 else float("inf")
        position = None
        next_player = 1 if player == 2 else 2

        for child_board, child_position in child_boards:
            _, child_value = self.alpha_beta(child_board, next_player, depth - 1, time_end, -beta, -alpha)
            child_value -= 1 if child_value > 0 else -1

            if player == 1:
                value, position = max( (value, position), (child_value, child_position) , key=lambda x : x[0])
                alpha = max(alpha, value)

            else:
                value, position = min((value, position), (child_value, child_position) , key=lambda x : x[0])
                beta = min(beta, value)

            if alpha >= beta:
                break


        if value <= alpha_origin:
            flag_to_save = "upperbound"
        elif value >= beta:
            flag_to_save = "lowerbound"
        else:
            flag_to_save = "exact"

        self.set(board, position, value, depth, flag_to_save)

        return position, value

    def heuristic(self, board, player : int) -> int:
        player_weights = {
            "4_open" : 1000,
            "4_semi" : 1000,
            "4_close" : 10,
            "3_open" : 1000,
            "3_semi" : 600,
            "3_close" : 150,
            "2_open" : 400,
            "2_semi" : 250,
            "2_close" : 5
        }

        opponent_weights = {
            "4_open" : 1000,
            "4_semi" : 500,
            "4_close" : 10,
            "3_open" : 300,
            "3_semi" : 150,
            "3_close" : 10,
            "2_open" : 80,
            "2_semi" : 40,
            "2_close" : 5
        }

        player_1 = self.get_k_row(board, player)
        player_2 = self.get_k_row(board, 1 if player == 2 else 2)
        scale = 1000
        count = sum(weight * player_1.get(key, 0) -  opponent_weights[key] * player_2.get(key, 0) for key, weight in player_weights.items())
        return math.trunc(61 * (count if -scale <= count <= scale else -scale if count < 0 else scale  )  / scale)

    def get_k_row(self, board, player) -> Dict[str, int]:
        count_k_row = {}
        ban_positions = {}

        for k in range(4, 1, - 1):
            positions = self.k_rows(board, player, k)
            valid_positions = {key: {value for value in positions if value not in ban_positions.get(Solver.get_key(key, alone = True), set())} for key, positions in positions.items()}

            for key, value in valid_positions.items():
                count_k_row[Solver.get_key(key, False)] = count_k_row.setdefault(Solver.get_key(key, False), 0) + len(value)

                ban_positions.setdefault(Solver.get_key(key, alone = True), set()).update(Solver.extend_ban_position(board, value, k, Solver.get_key(key, alone=True)))

        #print(count_k_row)
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