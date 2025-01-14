from datetime import datetime, timedelta
from board import Board
from typing import *
import math


class AI:

    def __init__(self, board : Board, time_to_play : float = 5):
        self.win_weight = int(board.total_pawn / 2 + 1)
        self.transposition_table = {}
        self.time_to_play = time_to_play
        self.iterative = 1



    def store_board(self, board : Board, move : str, value : float, depth : int, flag : str) -> None :
        self.transposition_table[board.key] = (move, value, depth, flag)

    def get_board(self, board : Board) -> Optional[Tuple[str, float, int, str]]:
        keys = board.rotated_key()
        for index, key in enumerate(keys):
            stored_value = self.transposition_table.get(key, None)
            if stored_value is not None:
                if 0 < index:
                    return board.turn_move(stored_value[0], index), stored_value[1], stored_value[2], stored_value[3]
                return stored_value
        return None

    def search(self, board : Board, player : int, previous_move : str) -> Tuple[float, Optional[str], str]:
        end = datetime.now() + timedelta(seconds=self.time_to_play) - timedelta(seconds= 0.01)

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
                board_copy = board.copy()
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


    def negamax(self, board: Board, depth: int, player: int, end_time : datetime, previous_move, alpha: int = -float("inf"), beta: int = float("inf"), display = False) -> Tuple[float, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), previous_move, "exact"

        board_saved = self.get_board(board)
        if board_saved is not None and (board_saved[2] >= depth or board_saved[3] == "exact"):
            return board_saved[1], board_saved[0], board_saved[3]

        if depth == 0 or datetime.now() > end_time:
            return AI.normalize_value(board.heuristic_value), previous_move, "heuristic" #self.normalize_value(board.heuristic_value)

        value_child, child_moves = AI.get_child_mouvs(board, player)
        if value_child is not None:
            return value_child, child_moves[0], "exact"
        depth -= 1
        next_player = 1 if player == 2 else 2
        best_value = -float("inf")
        best_move = child_moves[0]
        flag = "heuristic"

        for child_move in child_moves:
            board.play_to(player, child_move)
            value, _, child_flag = self.negamax(board, depth, next_player, end_time, child_move, -beta, -alpha)
            value = -value
            board.undo_to(child_move, player)

            value += 1 if value < 0 else -1 if value > 0 else 0

            if value > best_value:
                best_value = value
                best_move = child_move
                flag = child_flag

            alpha = max(alpha, best_value)

            if alpha >= beta or alpha == self.win_weight or beta == -self.win_weight:
                break

        self.store_board(board, best_move, best_value, depth, flag)

        return best_value, best_move, flag


    def alphabeta(self, board: Board, depth: int, player: int, end_time : datetime, previous_move, alpha: int = -float("inf"), beta: int = float("inf"), display = False) -> Tuple[float, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), previous_move, "exact"

        board_saved = self.get_board(board)
        if board_saved is not None and (board_saved[2] >= depth or board_saved[3] == "exact"):
            return board_saved[1], board_saved[0], board_saved[3]

        if depth == 0 or datetime.now() > end_time:
            return AI.normalize_value(board.heuristic_value), previous_move, "heuristic"

        value_child, child_moves = AI.get_child_mouvs(board, player)
        if value_child is not None:
            return value_child, child_moves[0], "exact"
        depth -= 1
        next_player = 1 if player == 2 else 2
        best_value = -float("inf") if player == 1 else float("inf")
        best_move = child_moves[0]
        flag = "heuristic"

        for child_move in child_moves:
            board.play_to(player, child_move)
            value, _, child_flag = self.alphabeta(board, depth, next_player, end_time, child_move, alpha, beta)
            board.undo_to(child_move, player)

            value += 1 if value < 0 else -1 if value > 0 else 0

            if player == 1:
                if value > best_value:
                    best_value = value
                    best_move = child_move
                    flag = child_flag

                alpha = max(alpha, best_value)

            else:
                if value < best_value:
                    best_value = value
                    best_move = child_move
                    flag = child_flag

                beta = min(beta, best_value)

            #print(f"{previous_move} : {child_move} {value}")

            if alpha >= beta or alpha == self.win_weight or beta == -self.win_weight:
                break

        #print(f"Final value : {previous_move} : {best_value}")
        self.store_board(board, best_move, best_value, depth, flag)

        return best_value, best_move, flag

    @staticmethod
    def get_child_mouvs(board : Board, player : int) -> Tuple[Optional[float], List[str]]:
        value, moves = board.forced_moves_opti(player)
        if moves is not None :
            moves = list(moves)
            moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)
            return value, moves

        if board.rule == "long pro" and board.pawn_played == 2:
            moves = board.can_play

        else :
            moves = [mouv for k_range in board.find_1_to_k_near_position(2) for mouv in k_range]
        moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)

        if len(moves) > 20:
            moves = moves[:20]

        return None, moves

    @staticmethod
    def normalize_value(n: float) -> float:
        return math.tanh(-n / 1_000_000_000)