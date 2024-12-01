from board import Board
import random

# Chaque joueur est limité a 60 pions !!!
board = Board()
print(board)

a = None
player = random.randint(1, 2)
player_moves = [[], []]
while board.is_winning is None and len(player_moves[0]) < 61 and len(player_moves[1]) < 61:

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

winner = board.is_winning
if winner in [-1, 1]:
    print(f"Congratulation Player {winner} wins")
else :
    print(f"It's a draw")
