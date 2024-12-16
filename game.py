from board import Board
from solver import Solver
import random
from datetime import datetime, timedelta

board = Board()
solver = Solver(60)



"""
position = 11972712782478197656684065389945465735878816944881664
mask = 23197056791886802764037326099063525452542046566875136
board.position = position
board.mask = mask

print(board)

start = datetime.now()

print(solver.solve(board, 2, "G3" ))

end = datetime.now()



print(f"delta = {end - start}")

"""


print(board)
a = None
player = 1
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
        move = solver.solve(board, 2, player_moves[0][-1])
        board.play_to(2, move)
        player_moves[player - 1].append(move)

    player = 1 if player == 2 else 2
    print(board)

winner = board.is_winning
if winner in [-1, 1]:
    print(f"Congratulations Player {winner} wins")
else :
    print(f"It's a draw")





