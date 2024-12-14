from board import Board
from solver import Solver
import random
from datetime import datetime, timedelta

board = Board()
solver = Solver()
board.play_to(1, "h7")

"""
position = 11972712782478197656684065389945465735878816944881664
mask = 23197056791886802764037326099063525452542046566875136
board.position = position
board.mask = mask
"""
print(board)


start = datetime.now()

k_near = board.find_1_to_k_near_position()

for i, near in enumerate(k_near, 1) :
    print(f"{i} : {near}")

child = Solver.get_child_boards(board, 1, "h7", 1)

for board in child:
    print(board[1], end=" ")

print()

end = datetime.now()



print(f"delta = {end - start}")
















"""


print(board)
b = Solver.find_1_to_k_near_position(board, 4)
for i, k_near in enumerate(b):
    print(f"{i} : {k_near}")
a = None
player = 1
player_moves = [[], []]
while board.is_winning is None:

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

    player = 1 if player == 2 else 2
    print(board)
    b = Solver.find_1_to_k_near_position(board, 4)
    for i, k_near in enumerate(b):
        print(f"{i} : {k_near}")

winner = board.is_winning
if winner in [-1, 1]:
    print(f"Congratulation Player {winner} wins")
else :
    print(f"It's a draw")
"""




