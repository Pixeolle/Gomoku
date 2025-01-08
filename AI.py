from datetime import datetime, timedelta
from joblib import Parallel, delayed
from board import Board
from typing import *
import math

class AI:

    def __init__(self, board : Board):
        self.win_weight = int(board.total_pawn / 2 + 1)
        self.transposition_table = {}
        self.prunning = 0
        self.tot = 0
        self.tree = {}
        self.iterative = 1

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

    def search(self, board : Board, player : int, value_board : int) -> Tuple[float, Optional[str], str]:
        best_move = None
        best_value = None
        best_flag = None
        depth = self.iterative
        remaining_moves = board.remaining_moves

        end = datetime.now() + timedelta(seconds=5)

        try:
            while datetime.now() < end and depth <= remaining_moves:
                value, move, flag = self.negamax(board.copy(), depth, player, end, value_board)
                if move is not None:
                    best_move = move
                    best_value = value
                    best_flag = flag
                depth += 1

        except TimeoutError:
            pass

        if depth - 1 < remaining_moves - 2: # Si on a atteint la fin on ne depasse pas le nombre de coup maximal car le prochain coup n'entrera pas dans la boucle while
            self.iterative = depth - 1
        print(f"Depth = {self.iterative + 1}")

        return best_value, best_move, best_flag


    def negamax(self, board: Board, depth: int, player: int, end_time : datetime, value_board : int,  alpha: int = -float("inf"), beta: int = float("inf")) -> Tuple[float, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), None, "exact"


        if depth == 0 or datetime.now() > end_time:
            return value_board / 100000, None, "heuristic"

        child_moves = self.get_child_mouvs(board, player, value_board)
        depth -= 1 if len(child_moves) > 3 else 0
        next_player = 1 if player == 2 else 2
        best_value = -float("inf")
        best_move = child_moves[0]
        flag = "exact"

        for child_move in child_moves:
            board.play_to(player, child_move)
            value, _, child_flag = self.negamax(board, depth, next_player, end_time, value_board, -beta, -alpha)
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


    def negamax_pool(self, board: Board, depth: int, player: int, end_time: datetime, value_board: int,
                alpha: int = -float("inf"), beta: int = float("inf")) -> Tuple[float, Optional[str], str]:

        winner = board.is_winning
        if winner is not None:
            return winner * (self.win_weight + 1), None, "exact"

        if depth == 0 or datetime.now() > end_time:
            return value_board / 100000, None, "heuristic"

        child_moves = self.get_child_mouvs(board, player, value_board)
        depth -= 1 if len(child_moves) > 3 else 0
        next_player = 1 if player == 2 else 2
        best_value = -float("inf")
        best_move = child_moves[0]
        flag = "exact"

        # Évaluation parallèle des coups
        results = Parallel(n_jobs=2)(
            delayed(self.negamax)(
                board.copy(),  # Une copie pour chaque processus
                depth,
                next_player,
                end_time,
                value_board,
                -beta,
                -alpha
            ) for child_move in child_moves[:2]  # Évalue les 2 premiers coups en parallèle
        )

        # Évaluation séquentielle des coups restants
        for i, child_move in enumerate(child_moves):
            if i < 2:  # Utilise les résultats déjà calculés en parallèle
                value, _, child_flag = results[i]
                value = -value
            else:  # Calcule les coups restants normalement
                board.play_to(player, child_move)
                value, _, child_flag = self.negamax_pool(board, depth, next_player, end_time, value_board, -beta, -alpha)
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

    def get_child_mouvs(self, board : Board, player : int, board_value : int, display = False) -> List[str]:
        moves = board.forced_moves(player)
        if moves is not None :
            return moves

        moves = [mouv for k_range in board.find_1_to_k_near_position(2) for mouv in k_range]
        moves.sort(key=lambda x : board.heuristic(board_value, x, player), reverse= (player == 1))

        if display :
            print(f"Value : {board_value} |", end="")
            for mouvement in moves:
                print(f"{mouvement} : {board.heuristic(board_value, mouvement, player)} | ", end="")
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