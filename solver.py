import math
import random
import numpy as np
from typing import *

from cupyx.fallback_mode.fallback import ndarray
from numpy.f2py.crackfortran import groupbegins90

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

    def solve(self, board: Board, player: int, previous_move) -> str:
        time_end : datetime = datetime.now() + timedelta(seconds= self.timeout - self.offset)
        best_move = board.can_play[0]

        depth = 4
        while datetime.now() < time_end and depth <= 4:
            best_move_find, value,_ = self.alpha_beta(board, [previous_move], player, depth, time_end)
            print(best_move_find)
            if best_move_find is not None:
                best_move = best_move_find
            print(f"Profondeur = {depth}, Mouvement = {best_move_find}, Valeur = {value}")
            depth += 1

        return best_move

    def alpha_beta(self, board : Board, previous_move : List[str], player : int, depth : int, time_end : datetime, alpha : int = -float("inf"), beta : int = float("inf")) -> Tuple[List[str], int, int]:
        alpha_origin = alpha
        board_saved = self.get(board)

        #print(f"Depth = {depth}")
        #print(previous_move)
        #print("Hello")
        #print(f"{previous_move=}")

        if Solver.is_saved_deeper_or_equal(board_saved, depth):
            if board_saved[2] == "exact":

                #print(previous_move.append(board_saved[0]))
                return previous_move, board_saved[1], depth
            elif board_saved[2] == "lowerbound":
                alpha = max(alpha, board_saved[1])
            elif board_saved[2] == "upperbound":
                beta = min(beta, board_saved[1])

            if alpha >= beta:
                return [board_saved[0]], board_saved[1], depth

        winner = board.is_winning
        if winner is not None:
            #print("Final State find")
            return previous_move, 61 * winner, depth

        if depth == 0 or datetime.now() >= time_end:
            #print(previous_move)
            return previous_move, 0, 0

        value, position, remaining_depth = self.evaluate_child_boards(board, previous_move, player, depth, time_end, alpha, beta)

        flag_to_save = self.determine_flag_to_save(value, alpha_origin, beta)

        self.set(board, position, value, depth, flag_to_save)

        return position, value, remaining_depth

    @staticmethod
    def is_saved_deeper_or_equal(board_saved : Tuple[str, int, int, str], depth : int):
        return board_saved is not None and board_saved[2] >= depth

    def evaluate_child_boards(self, board : Board, previous_move : List[str], player : int, depth : int, time_end : datetime, alpha : int, beta : int):
        child_movs = Solver.get_child_boards(board, previous_move, depth - 1)
        value = -float("inf") if player == 1 else float("inf")
        next_player = 1 if player == 2 else 2
        position = None
        remaining_depth = 0

        print(f"{previous_move} {child_movs}")

        child_index = 0
        while child_index < len(child_movs) and datetime.now() <= time_end:

            move_line = previous_move + [child_movs[child_index]]
            child_board = board.copy().play_to(player, child_movs[child_index])
            _, child_value, remaining_depth = self.alpha_beta(child_board, move_line, next_player, depth - 1, time_end, -beta, -alpha)


            child_value = Solver.adjust_child_value(child_value)

            if player == 1:
                value, position, alpha = Solver.evaluate_max(value, position, alpha, child_value, child_movs[child_index])
            else:
                value, position, beta = Solver.evaluate_min(value, position, beta, child_value, child_movs[child_index])

            print(f"{position} {value} {alpha} {beta}")
            if alpha >= beta or alpha > 60 or beta < -60:
                print(f"Cut : {len(child_movs) - 1 - child_index}")
                break

            child_index += 1

        return value, position, remaining_depth

    @staticmethod
    def get_child_boards(board, previous_move : List[str], depth : int) -> List[str]:
        def fill_depth(total_point : int, index : int) -> Tuple[int, int]:
            new_depth = np.ceil(total_point / (len(range_point) - index))
            total_point -= new_depth
            return new_depth, total_point

        def right_key(raw_key : int):
            keys = sorted(threshold.keys(), reverse=True)
            for key in keys:
                if key < raw_key:
                    return key
            return keys[-1]

        threshold = {
            0 : 1,
            4 : 2,
            5 : 3,
            8 : 4,
            10 : 6,

        }

        child_mouv = board.find_1_to_k_near_position()
        sorted_child_mouv = [sorted(k_near, key=lambda x: board.distance(x, previous_move[-1])) for k_near in child_mouv]
        range_point = [mouv for k_range in sorted_child_mouv[:threshold[right_key(depth)]] for mouv in k_range]
        #if len(range_point) > 1:
        #flat_child_mouv = [mouv for k_range in range_point for mouv in k_range]

        flat_child_mouv = range_point
        total_depth = len(flat_child_mouv)



        #asociated_depth = np.zeros([1] * len(flat_child_mouv), dtype=int)
        #for index in range(len(range_point)):
        #    asociated_depth[index], total_depth = fill_depth(total_depth, index)

        return flat_child_mouv

    @staticmethod
    def adjust_child_value(child_value):
        return child_value - 1 if child_value > 0 else child_value + 1 if child_value < 0 else child_value

    @staticmethod
    def evaluate_max(value, position, alpha, child_value, child_position):
        value, position = max((value, position), (child_value, child_position), key=lambda x: x[0])
        alpha = max(alpha, value)
        return value, position, alpha

    @staticmethod
    def evaluate_min(value, position, beta, child_value, child_position):
        value, position = min((value, position), (child_value, child_position), key=lambda x: x[0])
        beta = min(beta, value)
        return value, position, beta

    def determine_flag_to_save(self, value, alpha_origin, beta):
        if value <= alpha_origin:
            return "upperbound"
        elif value >= beta:
            return "lowerbound"
        else:
            return "exact"


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

    def find_intuition(self, p1, o1, p2, o2):
        self.winner((p1, o1), (p2, o2))
        return

    def winner(self, player_1 : Tuple[Dict[str, int], Dict[str, int]], player_2 : Tuple[Dict[str, int], Dict[str, int]], best_of : int = 1):
        score = [0, 0]
        while score[0] < best_of // 2 + 1 and score[1] < best_of // 2 + 1:
            score[self.match_result(player_1, player_2)] += 1

        return player_1 if score[0] > score[1] else player_2

    def match_result(self, player_1, player_2):
        board = Board()
        player = random.randint(1, 2)
        count = 1
        while board.is_winning is None:

            if player == 1:
                move = self.find_move_heuristic(board, player_1, 1)
                board.play_to(1, move)

            else :
                move = self.find_move_heuristic(board, player_2, 2)
                board.play_to(2, move)

            print(board)
            player = 1 if player == 2 else 2
            count += 1

        winner = board.is_winning
        print(f"Le joueur {winner} à gagné en {count} coups")
        return 0 if winner == 1 else 1

    def find_move_heuristic(self, board, weights, player) -> str:
        childs_board = self.get_child_boards(board, player)


        for child_board in childs_board:
            if child_board[0].is_winning == 1 and player == 1 or child_board[0].is_winning == -1 and player == 2:
                return child_board[1]

        positions = [position for _, position in childs_board]
        heuristics = [self.heuristic_train(child_board, player, weights[0], weights[1]) for child_board, _ in childs_board]
        print(f"{heuristics=}")
        print(f"{positions=}")

        print(f"Joueur {player} coup {positions[heuristics.index(max(heuristics) if player == 1 else  min(heuristics))]} : valeur = {max(heuristics) if player == 1 else  min(heuristics)}")

        return positions[heuristics.index(max(heuristics) if player == 1 else  min(heuristics))]

        total = sum(heuristics)
        probabilities = [h / total if total != 0 else 1 for h in heuristics]

        return random.choices(positions, weights=probabilities, k=1)[0]

    def heuristic_train(self, board, player : int, player_weights, opponent_weights) -> int:
        player_1 = self.get_k_row(board, player)
        player_2 = self.get_k_row(board, 1 if player == 2 else 2)
        scale = 100
        count = sum(weight * player_1.get(key, 0) -  opponent_weights[key] * player_2.get(key, 0) for key, weight in player_weights.items())
        return math.trunc(61 * (count if -scale <= count <= scale else -scale if count < 0 else scale  )  / scale)

