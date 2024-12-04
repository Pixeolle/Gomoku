from board import Board
from solver import Solver
import random
from datetime import datetime, timedelta

board = Board(8, 8)
solver = Solver()
"""
position = 11972712782478197656684065389945465735878816944881664
mask = 23197056791886802764037326099063525452542046566875136
board.position = position
board.mask = mask
"""
print(board)

a = None
player = random.randint(1, 2)
player_moves = [[], []]
while board.is_winning is None:

    if player == 1:
        is_valid = False
        while not is_valid:
            try:
                print(f"Player {player}'s turn")
                a = input()
                board.play_to(player, a)
                is_valid = True
                player_moves[player - 1].append(a)

            except ValueError as e:
                print(f"Error : {e}")

    else :
        move = solver.solve(board, player)
        board.play_to(player, move)
        player_moves[player - 1].append(move)

    player = 1 if player == 2 else 2
    print(board)
    Solver.k_rows(board, 1 if player == 2 else 2, 3)

winner = board.is_winning
if winner in [-1, 1]:
    print(f"Congratulation Player {winner} wins")
else :
    print(f"It's a draw")
