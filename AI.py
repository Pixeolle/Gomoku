from datetime import datetime, timedelta
from board import Board
from typing import *
import math

class AI:

    def __init__(self, board : Board, time_to_play : int = 5):
        self.win_weight = int(board.total_pawn / 2 + 1)
        self.transposition_table = {}
        self.time_to_play = time_to_play
        self.iterative = 1
        self.prunning = 0
        self.tot = 0
        self.tree = {}

    def store_board(self, board : Board, move : str, value : int) -> None :
        self.transposition_table[board.key] = (move, value)

    def get_board(self, board : Board) -> Optional[Tuple[str, int]]:
        keys = board.rotated_key()
        for index, key in enumerate(keys):
            stored_value = self.transposition_table.get(key, None)
            if stored_value is not None:
                if 0 < index < 4:
                    print("Symetrie trouvé")
                    return board.turn_move(stored_value[0], index), stored_value[1]
                return stored_value
        return None

    def search(self, board : Board, player : int, previous_move : str) -> Tuple[float, Optional[str], str]:
        if board.pawn_played == 0:
            return 0, "H7", "None"

        best_move = None
        best_value = None
        best_flag = None
        depth = self.iterative
        remaining_moves = board.remaining_moves

        end = datetime.now() + timedelta(seconds=self.time_to_play) - timedelta(seconds= 0.01)

        try:
            while datetime.now() < end and depth <= remaining_moves:
                value, move, flag = self.negamax(board.copy(), depth, player, end, previous_move)
                if move is not None:
                    best_move = move
                    best_value = value
                    best_flag = flag
                depth += 1

        except TimeoutError:
            pass

        if depth - 1 < remaining_moves - 2:
            self.iterative = depth - 1
        print(f"Depth = {self.iterative + 1}")

        return best_value, best_move, best_flag


    def negamax(self, board: Board, depth: int, player: int, end_time : datetime, previous_move, alpha: int = -float("inf"), beta: int = float("inf")) -> Tuple[float, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), previous_move, "exact"


        if depth == 0 or datetime.now() > end_time:
            return board.heuristic_value / 100000, previous_move, "heuristic"

        child_moves = self.get_child_mouvs(board, player)
        depth -= 1 if len(child_moves) > 3 else 0
        next_player = 1 if player == 2 else 2
        best_value = -float("inf")
        best_move = child_moves[0]
        flag = "exact"

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

    def alphabeta_open(self, board : Board, depth : int, player : int, alpha : int = -float("inf"), beta : int = float("inf"), keys : List[str] = None) -> Tuple[int, Optional[str], str]:

        if keys is None:
            self.tree = {}
            keys = []

        winner = board.is_winning
        if winner is not None:
            self.tot += 1
            return winner * (self.win_weight + 1) , None, "exact"

        saved_board = self.get_board(board)
        if saved_board is not None:
            self.tot += math.prod(range(len(board.can_play), len(board.can_play) - depth, -1))
            self.prunning += math.prod(range(len(board.can_play), len(board.can_play) - depth, -1))
            return saved_board[1], saved_board[0], "saved"

        if depth == 0:
            self.tot += 1
            return 0, None, "heuristic"

        child_moves = self.get_child_mouvs(board, player, 0)
        next_player = 1 if player == 2 else 2
        best_move = None
        flag = ""
        depth -= 1 if len(child_moves) > 3 else 0

        for index, child_move in enumerate(child_moves, 1):
            board.play_to(player, child_move)
            new_keys = keys.copy()
            new_keys.append(child_move)
            self.add_to_tree(new_keys, {})
            value,_, child_flag = self.alphabeta_open(board, depth, next_player, alpha, beta, new_keys)
            board.undo_to(child_move)

            value += 1 if value < 0 else - 1 if value > 0 else 0

            new_key = f"{new_keys[-1]} : {value}"
            self.change_key(new_keys, new_key)
            new_keys.pop()
            new_keys.append(new_key)

            if player == 1:
                if alpha < value:
                    alpha = value
                    best_move = child_move
                    flag = child_flag
            else:
                if beta > value:
                    beta = value
                    best_move = child_move
                    flag = child_flag

            if  alpha >= beta or alpha == self.win_weight or beta == -self.win_weight :
                self.tot += (len(child_moves) - index) * math.prod(range(len(board.can_play), len(board.can_play) - depth, -1))
                self.prunning += (len(child_moves) - index) * math.prod(range(len(board.can_play), len(board.can_play) - depth, -1))
                self.change_key(new_keys, f"{new_keys[-1]} : {'alpha' if player == 1 else 'beta'}")
                break

        board_rating = alpha if player == 1 else beta

        if flag == "exact" or flag == "saved":
            self.store_board(board, best_move, board_rating)

        return board_rating , best_move, flag

    def get_child_mouvs(self, board : Board, player : int, display = False) -> List[str]:
        moves = board.forced_moves_opti(player)
        if moves is not None :
            moves = list(moves)
            moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)
            if display :
                for mouvement in moves:
                    print(f"{mouvement} : {board.update_alignment(player, board.coordinate_to_bit(mouvement), True)} | ", end="")
                print()
            return moves

        moves = [mouv for k_range in board.find_1_to_k_near_position(2) for mouv in k_range]
        moves.sort(key=lambda x : board.update_alignment(player, board.coordinate_to_bit(x), True), reverse=True)

        if display :
            for mouvement in moves:
                print(f"{mouvement} : {board.update_alignment(player, board.coordinate_to_bit(mouvement), True)} | ", end="")
            print()

        if len(moves) > 10:
            moves = moves[:10]

        return moves

    def add_to_tree(self, keys, value):
        tree = self.tree
        for key in keys[:-1]:
            tree = tree.setdefault(key, {})
        tree[keys[-1]] = value

    def get_from_tree(self, keys):
        tree = self.tree
        for key in keys:
            tree = tree[key]
        return tree

    def change_key(self, old_key, new_key):
        tree = self.get_from_tree(old_key[:-1])
        value = tree.pop(old_key[-1])
        tree[new_key] = value