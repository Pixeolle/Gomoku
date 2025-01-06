import winsound
from board import Board
from AI import AI
from solver import Solver
import random
from datetime import datetime, timedelta


def average_elapsed_time(n = 1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            total_time = timedelta()
            for _ in range(n):
                start_time = datetime.now()
                result = func(*args, **kwargs)
                end_time = datetime.now()
                total_time += end_time - start_time
            average_time = total_time / n
            print(f"Function {func.__name__} took on average {average_time} seconds to execute over {n} runs.")
            return result
        return wrapper
    return decorator

all_rows = (11972712782478197656684065389945465735878816944881664, 23197056791886802764037326099063525452542046566875136)
check_defense = (5192376087906286159226792757428224, 510431338905924868895035403188574355456)

def generate_board_id():

    board = Board()
    #board.position = 45718620351076546948843949308563138826916069376
    #board.mask = 1712841491893727920171248923237171650074924548096
    #board.key = 92356230541475279300523438875616598032420803406933750624156058529001659443532863658820304698955891410492072392654848
    print(board)
    player = 1
    input_player = ""
    while input_player.lower().strip() != "stop" and board.is_winning is None:

        move_valid = False
        while not move_valid:
            try:
                input_player = input("")
                if input_player != "stop" and input_player != "invert":
                    board.play_to(player, input_player)
                    player = 1 if player == 2 else 2
                move_valid = True
            except Exception as e:
                print(f"Error : {e}")

        print(board)
        print(f"Position : {board.position}")
        print(f"Mask : {board.mask}")
        print(f"Key : {board.key}")
        start = datetime.now()
        a = board.forced_mouvs(player)
        time_elapsed = datetime.now() - start
        print(f"Time = {time_elapsed}")
        print(f"{a}")
    print(f"Winner = {board.is_winning}")



    return board.position, board.mask

def remaining_moves(board : Board, depth : int) -> int:
    count = 1
    for i in range(len(board.can_play), len(board.can_play) - depth, -1):
        count *= i
    return count

@average_elapsed_time(1)
def alpha_beta_test(board_setting, depth, player):
    board = Board()
    ai = AI(board)
    board.position = board_setting[0]
    board.mask = board_setting[1]
    print(board)

    print(f"\n La position trouvé est {ai.alphabeta(board, depth, player)}")
    print(f"{len(board.can_play)} : {remaining_moves(board, depth)}")
    print(f"{ai.prunning} coups ont été évité soit {ai.prunning / (remaining_moves(board, depth)):.4%} ")
    print(f"Transposition table : {ai.transposition_table}")

    ai.prunning = 0
    board.position = board_setting[0]
    board.mask = board_setting[1]
    print(board)
    start = datetime.now()
    print(f"\n La position trouvé est {ai.alphabeta_open(board, depth, player)}")
    end = datetime.now()
    print(f"{len(board.can_play)} : {remaining_moves(board, depth)}")
    print(f"{ai.prunning} coups ont été évité soit {ai.prunning / (remaining_moves(board, depth)):.4%} ")
    print(f"la fonction a pris {end - start}")
    print(f"{ai.tree}")

def test():

    board = Board()
    move_list = board.can_play * 100

    start_copy = datetime.now()
    for move in move_list:
        board_1 = board.copy().play_to(1, move)

    end_copy = datetime.now()

    start_undo = datetime.now()
    for move in move_list:
        board.play_to(1, move)
        board.undo_to(move)
    end_undo = datetime.now()

    print(f"Undo : {end_undo - start_undo} Copy : {end_copy - start_copy} Gap : {min(end_undo - start_undo, end_copy - start_copy) / max(end_undo - start_undo, end_copy - start_copy)}")

def against_ai():
    board = Board()
    ai = AI(board)
    print(board)
    player = 1
    input_player = ""
    while input_player.lower().strip() != "stop" and board.is_winning is None:

        if player == 1:
            move_valid = False
            while not move_valid:
                try:
                    input_player = input("")
                    if input_player != "stop":
                        board.play_to(player, input_player)
                    move_valid = True
                except Exception as e:
                    print(f"Error : {e}")
        else:
            ai.prunning = 0
            ai.tot = 0
            start_former = datetime.now()
            move_former = ai.search(board, player)
            time_former = datetime.now() - start_former
            #winsound.Beep(440, 300)
            #print(f"Coups : {ai.prunning} soit {ai.prunning / ai.tot}")
            print(f"Value : {move_former[0]} | Move : {move_former[1]} | Flag : {move_former[2]} | Time : {time_former} ")
            board.play_to(player, move_former[1])


        print(board)
        """
        if player == 2:
            request_valid = False
            user_input = ""
            while not request_valid:
                user_input = input("Do you want to see the tree search (y/n)")
                if user_input.lower() == "y" or user_input.lower() == "n":
                    request_valid = True
                else:
                    print("Input not valid")
            if user_input == "y":
                nav_tree(ai)
                print(board)
        """

        player = 1 if player == 2 else 2


    return board.position, board.mask

def print_keys(dict):
    if len(dict.keys()) == 0:
        print("Empty")
        return
    for key, _ in dict.items() :
        print(f"| {key} ", end="")
    print("|")

def nav_tree(ai : AI):
    user_inputs = []
    user_input = ""
    current_dict = ai.tree
    print_keys(current_dict)

    while user_input != "out":

        is_valid = False
        key_link = {key[:key.find(' ')] : key for key in current_dict.keys()}
        key_values = [int(split_string(key)) for key in current_dict.keys()]
        print(key_values)

        while not is_valid:

            user_input = input()

            if user_input == "out":
                is_valid = True
            elif user_input == "back":
                if len(user_inputs) > 0:
                    user_inputs.pop()
                    is_valid = True
                    current_dict = ai.get_from_tree(user_inputs)
                    if len(user_inputs) > 0:
                        print(f"{user_inputs[-1]} : ", end="")
                    print_keys(current_dict)
                    if len(user_inputs) % 2 == 0:
                        print(f"Min : {min(key_values)}")
                    else :
                        print(f"Max : {max(key_values)}")
            elif not isinstance(current_dict, dict):
                print("Leaf")
            elif key_link.get(user_input, None) not in current_dict.keys():
                print(f"Error {user_input} is not a key")
            else :
                user_inputs.append(key_link[user_input])
                current_dict = ai.get_from_tree(user_inputs)
                print(f"{len(user_inputs)} {user_inputs[-1]} : ", end="")
                if isinstance(current_dict, dict):
                    print_keys(current_dict)
                else :
                    print(current_dict)
                if len(user_inputs) % 2 == 0:
                    print(f"Min : {min(key_values)}")
                else :
                    print(f"Max : {max(key_values)}")
                is_valid = True

def split_string(s):
    parts = s.split(' ')
    if len(parts) > 2:
        return ' '.join(parts[2:4]) if len(parts) > 3 else ' '.join(parts[2:])
    return ''

def test_forced_move():
    board = Board()
    board.position = 45718620351076546948843949308563138826916069376
    board.mask = 1712841491893727920171248923237171650074924548096
    board.key = 92356230541475279300523438875616598032420803406933750624156058529001659443532863658820304698955891410492072392654848
    n = 1
    total_time = timedelta()
    for _ in range(n):
        start_time = datetime.now()
        a = board.forced_mouvs(2)
        print(f"{a}")
        end_time = datetime.now()
        total_time += end_time - start_time
    average_time = total_time / n
    print(f"Average execution time over {n} runs: {average_time}")

#generate_board_id()
#test_forced_move()
against_ai()