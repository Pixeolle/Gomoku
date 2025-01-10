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
    board.position = 5192455329366965992581233513594880
    board.mask = 36346553393226136395067175341129728
    value_board = 0
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
        start = datetime.now()
        value_board = board.heuristic(value_board, input_player, 1 if player == 2 else 2)
        print(f"Temps : {datetime.now() - start}")
        print(f"Value Board : {value_board}")
        print(f"Position : {board.position}")
        print(f"Mask : {board.mask}")

        loop = 100

        start = datetime.now()
        for _ in range(loop):
            a = board.forced_moves(player)
        t_v1 = datetime.now() - start

        start = datetime.now()
        for _ in range(loop):
            b = board.forced_moves_opti(player, input_player)
        t_v2 = datetime.now() - start

        print(f"a = {a}")
        print(f"b : {b}")
        print(f"V1 : {t_v1 / loop} | V2 : {t_v2 / loop}")

        if t_v1 > timedelta(seconds=0):
            print(f"Gain : {1 - t_v2 / t_v1}")

        if a is not None and b is not None:
            a = set(a)
            if a.issubset(b):
                print("Correct")



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
    value_board = 0

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
                        value_board = board.heuristic(value_board, input_player, player)
                    move_valid = True
                except Exception as e:
                    print(f"Error : {e}")
        else:
            ai.prunning = 0
            ai.tot = 0
            start_former = datetime.now()
            move_former = ai.search(board, player, value_board)
            time_former = datetime.now() - start_former
            print(f"Value : {move_former[0]} | Move : {move_former[1]} | Flag : {move_former[2]} | Time : {time_former} ")
            board.play_to(player, move_former[1])
            value_board = board.heuristic(value_board, input_player, player)


        print(f"{board}")
        player = 1 if player == 2 else 2
        ai.get_child_mouvs(board, player, value_board, True)


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

    directions = [1, 15, 14, 16]
    patern = 0b011010
    patern_length = 6

    for direction in directions:
        x, y = 0, 0
        if direction == 1:
            x = -1
        elif direction == 15:
            y = -1
        elif direction == 14:
            x, y = 1, -1
        elif direction == 16:
            x, y = -1, -1

        for bit in range(225):
            line = 15 - bit % 15 - 1
            column =  15 - bit // 15 - 1
            if 15 > line + x * (patern_length - 1) >= 0 and 15 > column + y * (patern_length - 1) >= 0:
                board = Board()
                apply_patern = 0
                for i in range(patern_length):
                    if (patern >> i) & 1 == 1:
                        apply_patern |= (1 << i * direction + bit)

                board.position |= apply_patern
                board.mask |= apply_patern
                #print(board)
                a = board.forced_mouvs(1)
                print(a)

generate_board_id()
#test_forced_move()
#against_ai()

"""board = Board()
print(board.get_test())"""





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

# Sequence creant un None : H7 H8 G7 G8 F8 J8 I8 I9 F5 J9 F7 F6 E7 -> None