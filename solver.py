from board import Board
from datetime import datetime, timedelta

class Solver:

    def __init__(self):
        self.table = {}

    def set(self, board : Board, value : int, position : str, depth : int, flag : str):
        self.table[hash(board)] = (value, position, depth, flag)

    def get(self, board):
        return self.table.get(hash(board))

    def solve(self, board: Board, player: int):
        offset = 0.01
        time_end : datetime = datetime.now() + timedelta(seconds= 5 - offset)

        depth = 0
        while datetime.now() < time_end:
            #best_move = self.alpha_beta(board, player, depth)
            depth += 1

        return 0

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

    def heuristic(self, board):
        return 1


