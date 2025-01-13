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

        self.killer_moves = []
        for _ in range(board.total_pawn):
            self.killer_moves.append(set())


    def store_board(self, board : Board, move : str, value : float, depth : int, flag : str) -> None :
        self.transposition_table[board.key] = (move, value, depth, flag)

    def get_board(self, board : Board) -> Optional[Tuple[str, float, int, str]]:
        keys = board.rotated_key()
        for index, key in enumerate(keys):
            stored_value = self.transposition_table.get(key, None)
            if stored_value is not None:
                if 0 < index:
                    print("Symetrie trouvé")
                    return board.turn_move(stored_value[0], index), stored_value[1], stored_value[2], stored_value[3]
                print("Plateau trouvé")
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
                value, move, flag = self.negamax(board_copy, depth, player, end, previous_move)
                if move is not None:
                    best_move = move
                    best_value = value
                    best_flag = flag
                depth += 1

        except TimeoutError:
            pass

        if depth - 1 < remaining_moves - 2:
            self.iterative = depth - 1
        #print(f"Depth = {self.iterative + 1}")

        if board.pawn_played == 0:
            return 0, "H7", "None"

        return best_value, best_move, best_flag


    def negamax(self, board: Board, depth: int, player: int, end_time : datetime, previous_move, alpha: int = -float("inf"), beta: int = float("inf")) -> Tuple[float, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), previous_move, "exact"

        board_saved = None # self.get_board(board)
        if board_saved is not None and (board_saved[2] >= depth or board_saved[3] == "exact"):
            return board_saved[1], board_saved[0], board_saved[3]

        if depth == 0 or datetime.now() > end_time:
            return self.normalize_value(board.heuristic_value), previous_move, "heuristic"

        child_moves = self.get_child_mouvs(board, player)
        depth -= 1 if len(child_moves) > 3 else 0
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

    def negascout(self, board: Board, depth: int, player: int, end_time: datetime, alpha: float, beta: float) -> Tuple[int, Optional[str], str]:
        if datetime.now() > end_time:
            raise TimeoutError()

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), None, "exact"

        if depth == 0:
            return 0, None, "heuristic"

        stored = self.get_board(board)
        if stored is not None and depth > 0:
            return stored[1], stored[0], "saved"

        child_moves = self.get_child_mouvs(board, player, 0)
        next_player = 1 if player == 2 else 2
        best_value = -float("inf")
        best_move = None
        flag = "exact"
        n = beta

        for i, child_move in enumerate(child_moves):
            board.play_to(player, child_move)

            if i == 0:
                value, _, child_flag = self.negascout(board, depth - 1, next_player, end_time, -beta, -alpha)
                value = -value
            else:
                value, _, child_flag = self.negascout(board, depth - 1, next_player, end_time, -n, -alpha)
                value = -value

                if alpha < value < beta:
                    value, _, child_flag = self.negascout(board, depth - 1, next_player, end_time, -beta, -value)
                    value = -value

            board.undo_to(child_move)

            value += 1 if value < 0 else -1 if value > 0 else 0

            if value > best_value:
                best_value = value
                best_move = child_move
                flag = child_flag

            alpha = max(alpha, value)
            if alpha >= beta:
                break

            n = alpha + 1

        if flag == "exact":
            self.store_board(board, best_move, best_value)

        return best_value, best_move, flag

    def get_child_mouvs(self, board : Board, player : int, display = False) -> List[str]:
        moves = board.forced_moves_opti(player)
        if moves is not None :
            moves = list(moves)
            moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)
            return moves

        if board.rule == "long pro" and board.pawn_played == 2:
            moves = board.can_play
        else :
            moves = [mouv for k_range in board.find_1_to_k_near_position(2) for mouv in k_range]
        moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)

        if display :
            for mouvement in moves:
                print(f"{mouvement} : {board.update_alignment(player, board.coordinate_to_bit(mouvement), True)} | ", end="")
            print()

        if len(moves) > 10:
            moves = moves[:10]

        return moves

    def normalize_value(self, n: float) -> float:

        return math.tanh(-n / 1_000_000_000)