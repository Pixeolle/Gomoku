from datetime import datetime, timedelta
from board import Board
from typing import *
import math


class AI:
    def __init__(self, board: Board, time_to_play: float = 5):
        self.win_weight = int(board.total_pawn / 2 + 1)
        self.transposition_table = {}
        self.time_to_play = time_to_play
        self.iterative = 1

    def store_board(self, board: Board, move: str, value: float, depth: int, alpha: float, beta: float, flag: str) -> None:
        if value <= alpha:
            flag = "upperbound"
        elif value >= beta:
            flag = "lowerbound"
        else:
            flag = "exact"

        if -1 < value < 1 and flag == "exact":
            flag = "heuristic"

        value += 1 if value < 0 else -1 if value > 0 else 0
        self.transposition_table[board.key] = (move, value, depth, flag)

    def get_board(self, board: Board, depth: int, alpha: float, beta: float) -> Optional[Tuple[str, float, int, str]]:
        keys = board.rotated_key()
        for index, key in enumerate(keys):
            stored = self.transposition_table.get(key)
            if stored is not None:
                move, value, stored_depth, flag = stored

                if index > 0:
                    move = board.turn_move(move, index)

                if stored_depth >= depth:
                    if flag == "exact":
                        return move, value, stored_depth, flag
                    elif flag == "lowerbound" and value >= beta:
                        return move, value, stored_depth, flag
                    elif flag == "upperbound" and value <= alpha:
                        return move, value, stored_depth, flag

        return None

    def nullwindow_search(self, board: Board, depth: int, player: int, end_time: datetime, previous_move: str, beta: float) -> Tuple[float, Optional[str], str]:
        """Recherche avec fenêtre nulle (alpha = beta-1)"""
        return self.alphabeta(board, depth, player, end_time, previous_move, beta - 1, beta)

    def alphabeta(self, board: Board, depth: int, player: int, end_time: datetime, previous_move, alpha: float = -float("inf"), beta: float = float("inf")) -> Tuple[float, Optional[str], str]:
        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), previous_move, "exact"

        tt_result = self.get_board(board, depth, alpha, beta)
        if tt_result is not None:
            return tt_result[1], tt_result[0], tt_result[3]

        if depth == 0 or datetime.now() > end_time:
            return AI.normalize_value(board.heuristic_value), previous_move, "heuristic"

        value_child, child_moves = AI.get_child_mouvs(board, player)
        if value_child is not None:
            return value_child, child_moves[0], "exact"

        depth -= 1 if len(child_moves) > 3 else 0
        next_player = 1 if player == 2 else 2
        best_value = -float("inf") if player == 1 else float("inf")
        best_move = child_moves[0]
        flag = "exact"

        for i, child_move in enumerate(child_moves):
            board.play_to(player, child_move)

            if i == 0:
                value, _, child_flag = self.alphabeta(board, depth, next_player, end_time, child_move, alpha, beta)
            else:
                if player == 1:
                    value, _, child_flag = self.nullwindow_search(board, depth, next_player, end_time, child_move, alpha + 1)
                    if alpha < value < beta:
                        value, _, child_flag = self.alphabeta(board, depth, next_player, end_time, child_move, value - 1, beta)
                else:
                    value, _, child_flag = self.nullwindow_search(board, depth, next_player, end_time, child_move, beta)
                    if alpha < value < beta:
                        value, _, child_flag = self.alphabeta(board, depth, next_player, end_time, child_move, alpha, value + 1)

            board.undo_to(child_move, player)

            value += 1 if value < 0 else -1 if value > 0 else 0

            if player == 1:
                if value > best_value:
                    best_value = value
                    best_move = child_move
                alpha = max(alpha, best_value)
            else:
                if value < best_value:
                    best_value = value
                    best_move = child_move
                beta = min(beta, best_value)

            if alpha >= beta:
                break

        self.store_board(board, best_move, best_value, depth, alpha, beta, flag)
        return best_value, best_move, flag

    def search(self, board: Board, player: int, previous_move: str) -> Tuple[float, Optional[str], str]:
        end = datetime.now() + timedelta(seconds=self.time_to_play) - timedelta(seconds=0.01)
        best_move = None
        best_value = None
        best_flag = None
        board_copy = board.copy()
        depth = self.iterative
        remaining_moves = board.remaining_moves

        if board.pawn_played == 0:
            board_copy.play_to(player, "H7")

        try:
            while datetime.now() < end and depth <= remaining_moves:
                value, move, flag = self.alphabeta(board_copy, depth, player, end, previous_move)
                print(f"{depth} | {value} | {move} | {flag}")
                if move is not None:
                    best_move = move
                    best_value = value
                    best_flag = flag
                depth += 1

        except TimeoutError:
            pass

        if depth - 1 < remaining_moves - 2:
            self.iterative = depth - 1

        if board.pawn_played == 0:
            return 0, "H7", "open"

        return best_value, best_move, best_flag

    @staticmethod
    def get_child_mouvs(board : Board, player : int) -> Tuple[Optional[float], List[str]]:
        value, moves = board.forced_moves_opti(player)
        if moves is not None :
            moves = list(moves)
            moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)
            return None, moves

        if board.rule == "long pro" and board.pawn_played == 2:
            moves = board.can_play

        else :
            moves = [mouv for k_range in board.find_1_to_k_near_position(2) for mouv in k_range]
        moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)

        if len(moves) > 10:
            moves = moves[:10]

        return None, moves

    @staticmethod
    def normalize_value(n: float) -> float:
        return math.tanh(-n / 1_000_000_000)