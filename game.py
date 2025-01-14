import copy
from board import Board
from AI import AI
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
    #board.position = 5192455329366965992581233513594880
    #board.mask = 36346553393226136395067175341129728
    ai = AI(board)
    value_board = 0
    print(board)
    player = 1
    input_player = ""
    while input_player.lower().strip() != "stop" and board.is_winning is None:

        move_valid = False
        valid_copy = False
        while not move_valid:
            try:
                input_player = input("")
                if input_player != "stop" and input_player != "invert":
                    copy_value = copy.deepcopy(board.forced_bit_offset)
                    board.play_to(player, input_player)
                    board.undo_to(input_player, player)
                    if board.forced_bit_offset == copy_value:
                        valid_copy = True

                    board.play_to(player, input_player)
                    player = 1 if player == 2 else 2
                move_valid = True
            except ValueError as e:
                print(f"Error : {e}")


        print(board)
        print(f"Avant Forced : {board.forced_bit_offset}")
        print(f"Value Board : {board.heuristic_value}")

        a = board.forced_moves(player)
        b = board.forced_moves_opti(player)

        print(f"Undo : {valid_copy}")


        print(f"a : {a}")
        print(f"b : {b}")

        if a is not None and b is not None:
            a = set(a)
            if a.issubset(b):
                print("Correct")

        #ai.get_child_mouvs(board, player, True)


    print(f"Winner = {board.is_winning}")

    return board.position, board.mask



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
            move_former = ai.search(board, player, input_player)
            time_former = datetime.now() - start_former
            print(f"Value : {move_former[0]} | Move : {move_former[1]} | Flag : {move_former[2]} | Time : {time_former} ")
            board.play_to(player, move_former[1])


        print(f"{board}")
        player = 1 if player == 2 else 2
        print(f"Mouvs : {AI.get_child_mouvs(board, player)}")


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

def play_sequence(firstplayer, sequence):

    player = firstplayer
    board = Board()

    for i in sequence:
        board.play_to(player, i)
        player ^= 3

    print(board)
    print(f"Value Board : {board.heuristic_value}")

    a = board.forced_moves(player)
    b = board.forced_moves_opti(player)

    print(f"Avant Forced : {board.forced_bit_offset}")


    print(f"a : {a}")
    print(f"b : {b}")

    if a is not None and b is not None:
        a = set(a)
        if a.issubset(b):
            print("Correct")


sequence = ["H7","G8","H8","H9","F7","G9","G7","E7","I7","J7","I9","F6","J10","K11","I8","I6","G6","J9","F5","E4","H5","E8","H6","H4","G5","E5","E6" ]
#play_sequence(1, sequence)
#generate_board_id()
#test_forced_move()
against_ai()
#test()
"""
board = Board()
print(board.get_test())
"""


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