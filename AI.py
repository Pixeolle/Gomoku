import datetime
import math
from datetime import datetime, timedelta
from typing import *
from board import Board

class AI:

    def __init__(self, board : Board):
        self.win_weight = int(board.total_pawn / 2 + 1)
        self.transposition_table = {}
        self.prunning = 0
        self.tot = 0
        self.tree = {}

    def store_board(self, board : Board, move : str, value : int) -> None :
        self.transposition_table[board.key] = (move, value)

    def get_board(self, board : Board) -> Optional[Tuple[str, int]]:
        keys = board.rotated_key()
        keys.append(board.invert_key())
        for index, key in enumerate(keys):
            stored_value = self.transposition_table.get(key, None)
            if stored_value is not None:
                if 0 < index < 4:
                    print("Symetrie trouvé")
                    return board.turn_move(stored_value[0], index), stored_value[1]
                return stored_value
        return None

    def search(self, board : Board, player : int) -> Tuple[int, Optional[str], str]:
        best_move = None
        best_value = None
        best_flag = None
        depth = 1

        end = datetime.now() + timedelta(seconds=60)

        while datetime.now() < end :
            value, move, flag = self.alphabeta_open(board, depth, player)
            if best_value is None or value >= best_value:
                best_move = move
                best_value = value
                best_flag = flag

            depth += 1

        print(f"Depth = {depth}")

        return best_value, best_move, best_flag

    def alphabeta(self, board : Board, depth : int, player : int, alpha : int = -float("inf"), beta : int = float("inf")) -> Tuple[int, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1) , None, "exact"

        if depth == 0:
            return 0, None, "heuristic"

        child_moves = [mouv for k_range in board.find_1_to_k_near_position(2) for mouv in k_range]
        next_player = 1 if player == 2 else 2
        best_move = None
        flag = ""
        depth -= 1

        for index, child_move in enumerate(child_moves, 1):
            board.play_to(player, child_move)
            value,_, child_flag = self.alphabeta_open(board, depth, next_player, alpha, beta)
            board.undo_to(child_move)

            value += 1 if value < 0 else - 1 if value > 0 else 0

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
                break

        board_rating = alpha if player == 1 else beta

        return board_rating , best_move, flag

    def negamax_1(self, board : Board, depth : int, player : int, alpha : int = -float("inf"), beta : int = float("inf")) -> Tuple[int, Optional[str], str]:
        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1) , None, "exact"

        if depth == 0:
            return 0, None, "heuristic"

        child_moves = self.get_child_mouvs(board, player)
        next_player = 1 if player == 2 else 2
        print(f"{next_player=}")
        best_value = -self.win_weight
        best_move = None
        flag = ""
        depth -= 1

        for child_move in child_moves:
            board.play_to(player, child_move)
            value,_, child_flag = self.alphabeta_open(board, depth, next_player, -beta, -alpha)
            board.undo_to(child_move)

            value += 1 if value < 0 else - 1 if value > 0 else 0

            if best_value < -value:
                value *= -1 if player == 2 else 1
                alpha = max(alpha, value)
                best_move = child_move
                flag = child_flag

            if  alpha >= beta or alpha == self.win_weight or beta == -self.win_weight :
                break

        return best_value, best_move, flag


    def negamax(self, board: Board, depth: int, player: int, alpha: int = -float("inf"), beta: int = float("inf")) -> Tuple[int, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), None, "exact"


        if depth == 0:
            return 0, None, "heuristic"

        child_moves = self.get_child_mouvs(board, player)
        next_player = 1 if player == 2 else 2
        best_value = -float("inf")
        best_move = None
        flag = "exact"

        for child_move in child_moves:
            board.play_to(player, child_move)
            value, _, child_flag = self.negamax(board, depth - 1, next_player, -beta, -alpha)
            value = -value
            board.undo_to(child_move)

            value += 1 if value < 0 else -1 if value > 0 else 0

            if value > best_value:
                best_value = value
                best_move = child_move
                flag = child_flag

            alpha = max(alpha, best_value)

            if alpha >= beta or alpha == self.win_weight or beta == -self.win_weight:
                break

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

        child_moves = self.get_child_mouvs(board, player)
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
                self.change_key(new_keys, f"{new_keys[-1]} : {"alpha" if player == 1 else "beta"}")
                break

        board_rating = alpha if player == 1 else beta

        if flag == "exact" or flag == "saved":
            self.store_board(board, best_move, board_rating)

        return board_rating , best_move, flag

    def get_child_mouvs(self, board : Board, player : int) -> List[str]:
        mouvs = board.forced_mouvs(player)
        if mouvs is None :
            mouvs = [mouv for k_range in board.find_1_to_k_near_position(2) for mouv in k_range]

        mouvs = mouvs[:14]
        return mouvs

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