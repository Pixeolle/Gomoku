import os
import random
from typing import Tuple, Optional
from datetime import datetime
from pyfiglet import Figlet
from board import Board
from AI import AI
import threading


class GomokuGame:
    def __init__(self):
        self.board = Board()
        self.ai = AI(self.board)
        self.game_mode = None
        self.style_x = "\033[91mX\033[0m"
        self.style_o = "\033[94mO\033[0m"
        self.moves_history = []
        self.ia_timer = None
        self.voyager_thread = None
        self.voyager_running = False

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_title(self):
        print(Figlet(font='slant').renderText('Gomoku'))

    def display_menu(self) -> str:
        print("\n" + "═" * 50)
        print("Menu Principal:")
        print("1. Joueur contre Joueur")
        print("2. Joueur contre IA")
        print("3. IA contre IA")
        print("4. Règles du jeu")
        print("5. Voir une partie sauvegardée")
        print("6. Changer le mode de jeu")
        print("7. Quitter")
        print("═" * 50)
        return input("\nVotre choix (1-7): ")

    def select_game_mode(self) -> str:
        self.clear()
        self.display_title()
        print("\n" + "═" * 50)
        print("Sélection du mode de jeu:")
        print("1. Mode Normal")
        print("2. Mode Long Pro")
        print("═" * 50)

        while True:
            choice = input("\nVotre choix (1-2): ")
            if choice == "1":
                return "normal"
            elif choice == "2":
                return "long pro"
            else:
                print("Choix invalide! Veuillez choisir 1 ou 2.")

    def select_first_player(self, game_type: str = None) -> int:
        self.clear()
        self.display_title()
        print("\n" + "═" * 50)
        print("Qui commence la partie ?")
        if game_type == "pvp":
            print(f"1. Joueur 1 ({self.style_o})")
            print(f"2. Joueur 2 ({self.style_x})")
        elif game_type == "ai_vs_ai":
            print("1. IA 1")
            print("2. IA 2")
        else:
            print("1. Joueur")
            print("2. IA")
        print("3. Aléatoire")
        print("═" * 50)

        while True:
            choice = input("\nVotre choix (1-3): ")
            if choice in ["1", "2"]:
                return int(choice)
            elif choice == "3":
                first = random.randint(1, 2)
                if game_type == "ai_vs_ai":
                    print(f"\nL'IA {first} commence!")
                elif game_type == "pve":
                    print("\nLe joueur commence!" if first == 1 else "\nL'IA commence!")
                else:
                    print(f"\nLe joueur {first} commence!")
                input("\nAppuyez sur Entrée pour continuer...")
                return first
            else:
                print("Choix invalide! Veuillez choisir entre 1 et 3.")

    def display_rules(self):
        self.clear()
        rules_text = """ 
        Règles du Gomoku:
        ════════════════════════════════════════════════════════════════
        • Le jeu se joue sur un plateau de 15x15
        • Les joueurs placent leurs pions à tour de rôle
        • Le but est d'aligner 5 pions de sa couleur de n'importe quelle manière
        • Le premier joueur utilise les "\033[94mO\033[0m"
        • Le second joueur utilise les "\033[91mX\033[0m"
        
        Comment jouer ?
        • Entrez les coordonnées sous la forme 'A0' par exemple.
          - La lettre représente la ligne (A-O)
          - Le chiffre représente la colonne (0-14)
        """

        if self.game_mode == "normal":
            rules_text += """
        Règles du mode Normal:
        • Ouverture simple, vous pouvez jouer n'importe où au début
        ════════════════════════════════════════════════════════════════
        """

        if self.game_mode == "long pro":
            rules_text += """
        Règles additionnelles du mode long Pro:
        • En début de partie le premier joueur peut jouer n'importe où
        • Le deuxième joueur place ensuite un pion n'importe où
        • Ensuite, le premier joueur doit jouer dans un carré de 7x7 avec pour centre son premier coup.
        • Les joueurs continuent à jouer de façon classique
        ════════════════════════════════════════════════════════════════
        """
        print(rules_text)
        input("\nAppuyez sur Entrée pour revenir au menu !")

    def get_player_move(self, player: int) -> str:
        while True:
            try:
                if player == 1:
                    player_symbol = self.style_o
                else:
                    player_symbol = self.style_x
                move = input(f"\nJoueur {player} ({player_symbol}), entrez votre coup : ")
                if move.lower() == 'quit':
                    return move
                if move.upper() not in self.board.can_play:
                    print("Coup non valide ! Veuillez entrer un coup valide.")
                    continue
                self.moves_history.append(self.board.clean_move(move)[0])
                return move
            except ValueError as e:
                print(f"Erreur: {e}")

    def display_game_state(self, current_player: int, game_mode: str):
        self.clear()
        print(f"Mode: {game_mode} ({self.game_mode.upper()})")
        if current_player == 1:
            player_symbol = self.style_o
        else:
            player_symbol = self.style_x
        print(f"Tour du Joueur {current_player} ({player_symbol})")

        if game_mode == "Joueur contre IA" and current_player == 1 and self.ia_timer is not None:
            print(f"Temps de réflexion de l'IA: {self.ia_timer}")
        elif game_mode == "Joueur contre IA" and current_player == 2:
            print("Tour de l'IA....")

        print(self.board)
        print("Historique des 10 derniers coups : ")

        player1_moves = self.moves_history[::2][-10:]
        player2_moves = self.moves_history[1::2][-10:]

        print("Joueur 1:")
        for i, move in enumerate(player1_moves, start=1):
            print(f"{i:2d}. {move:<3}", end="   ")
            if i % 5 == 0:
                print()
        print()


        print("Joueur 2:")
        for i, move in enumerate(player2_moves, start=1):
            print(f"{i:2d}. {move:<3}", end="   ")
            if i % 5 == 0:
                print()
        print()

    def save_moves_to_file(self, filename: str):
        first_move = self.moves_history[0]
        first_player = "O (Joueur 1)" if self.moves_history.index(first_move) % 2 == 0 else "X (Joueur 2)"

        with open(f"{filename}.txt", "w") as file:
            file.write(f"Premier joueur : {first_player}\n")
            for i, move in enumerate(self.moves_history, start=1):
                file.write(f"{i}. {move}\n")
        print(f"\nHistorique des coups sauvegardé dans {filename}.txt")

    def ask_save_moves(self):
        check = False
        while not check:
            choice = input("\nVoulez-vous sauvegarder l'historique des coups ? (Oui/Non): ")
            if choice.lower() == 'oui' or choice.lower() == 'o':
                filename = input("Entrez le nom de la sauvegarde ").strip()
                self.save_moves_to_file(filename)
                check = True
            elif choice.lower() == 'non' or choice.lower() == 'n':
                print("\nHistorique des coups non sauvegardé.")
                check = True
            else:
                print("Choix invalide! Veuillez répondre par 'Oui' ou 'Non'.")

    def play_pvp(self):
        self.moves_history = []
        current_player = self.select_first_player(game_type="pvp")
        game_mode = "Joueur contre Joueur"

        while True:
            self.display_game_state(current_player, game_mode)

            move = self.get_player_move(current_player)
            if move.lower() == 'quit':
                break

            self.board.play_to(current_player, move)

            winner = self.board.is_winning
            if winner is not None:
                self.display_game_state(current_player, game_mode)
                if winner == 0:
                    print("\n═══ Match nul! ═══")
                else:
                    if current_player == 1:
                        player_symbol = self.style_o
                    else:
                        player_symbol = self.style_x
                    print(f"\n═══ Le Joueur {current_player} ({player_symbol}) a gagné! ═══")
                self.ask_save_moves()
                input("\nAppuyez sur Entrée pour revenir au menu...")
                break

            current_player = 3 - current_player

    def play_vs_ai(self):
        self.moves_history = []
        current_player = self.select_first_player(game_type="vs_ai")
        game_mode = "Joueur contre IA"
        self.ia_timer = None
        last_move = None

        while True:
            self.display_game_state(current_player, game_mode)

            if current_player == 1:
                self.start_voyager()
                move = self.get_player_move(current_player)
                last_move = move
                self.stop_voyager()
                if move.lower() == 'quit':
                    break
            else:
                start_timer = datetime.now()

                _, move, _ = self.ai.search(self.board, current_player, last_move)
                last_move = move
                end_timer = datetime.now()
                self.ia_timer = end_timer - start_timer
                if move is None:
                    print("L'IA n'a pas pu trouver de coup valide!")
                    break
                print(f"\nL'IA joue: {move}")
                self.moves_history.append(self.board.clean_move(move)[0])

            self.board.play_to(current_player, move)

            winner = self.board.is_winning
            if winner is not None:
                self.display_game_state(current_player, game_mode)
                if winner == 0:
                    print("\n═══ Match nul! ═══")
                elif winner == 1:
                    print("\n═══ Vous avez gagné contre l'IA! ═══")
                else:
                    print("\n═══ L'IA vous a écrasé! ═══")
                self.ask_save_moves()
                input("\nAppuyez sur Entrée pour revenir au menu...")
                break

            current_player = 3 - current_player

    def play_ai_vs_ai(self):
        self.moves_history = []
        current_player = self.select_first_player(game_type="ai_vs_ai")
        game_mode = "IA contre IA"
        value_board = 0

        while True:
            self.display_game_state(current_player, game_mode)

            _, move, _ = self.ai.search(self.board, current_player, value_board)
            if move is None:
                print(f"L'IA {current_player} n'a pas pu trouver de coup valide!")
                break

            print(f"\nL'IA {current_player} joue: {move}")
            self.moves_history.append(move)
            self.board.play_to(current_player, move)
            value_board = self.board.heuristic(value_board, move, current_player)

            winner = self.board.is_winning
            if winner is not None:
                self.display_game_state(current_player, game_mode)
                if winner == 0:
                    print("\n═══ Match nul! ═══")
                else:
                    print(f"\n═══ L'IA {current_player} a gagné! ═══")
                input("\nAppuyez sur Entrée pour continuer...")
                self.ask_save_moves()
                input("\nAppuyez sur Entrée pour revenir au menu...")
                break

            current_player = 3 - current_player

    def load_and_display_game(self):
        self.clear()
        self.display_title()
        filename = input("Entrez le nom de la sauvegarde à voir: ").strip()
        try:
            with open(f"{filename}.txt", "r") as file:
                lines = file.readlines()
                first_player_info = lines[0].strip()
                moves = [line.split(". ")[1].strip() for line in lines[1:]]
                self.board = Board()
                self.moves_history = []
                current_player = 1
                for move in moves:
                    self.board.play_to(current_player, move)
                    self.moves_history.append(move)
                    current_player = 3 - current_player

                print("\n" + "═" * 50)
                print(f"Partie sauvegardée: {filename}.txt")
                print(first_player_info)
                print(f"Nombre total de coups: {len(moves)}")
                print("═" * 50 + "\n")
                print(self.board)

                print("\nHistorique :")
                player1_moves = self.moves_history[::2]
                player2_moves = self.moves_history[1::2]

                print("\nJoueur 1:")
                for i, move in enumerate(player1_moves, start=1):
                    print(f"{i:2d}. {move:<3}", end="   ")
                    if i % 5 == 0:
                        print()
                print()

                print("\nJoueur 2:")
                for i, move in enumerate(player2_moves, start=1):
                    print(f"{i:2d}. {move:<3}", end="   ")
                    if i % 5 == 0:
                        print()
                print()

        except FileNotFoundError:
            print(f"\nErreur: Le fichier {filename}.txt n'existe pas.")
        except Exception as e:
            print(f"\nErreur lors de la lecture du fichier: {e}")

        input("\nAppuyez sur Entrée pour revenir au menu...")

    def voyager(self):
        print(f"TT avant voyager {len(self.ai.transposition_table)}")
        try:
            while self.voyager_running:

                board_copy = self.board.copy()
                _, move, _ = self.ai.search(board_copy, 2, self.moves_history[-1])
        except Exception as e:
            print(f"Erreur dans le thread Voyager: {e}")

        print(f"TT avant voyager {len(self.ai.transposition_table)}")

    def start_voyager(self):
        self.voyager_running = True
        self.voyager_thread = threading.Thread(target=self.voyager)
        self.voyager_thread.daemon = True
        self.voyager_thread.start()

    def stop_voyager(self):
        self.voyager_running = False
        if self.voyager_thread:
            self.voyager_thread.join(timeout=1)


    def run(self):
        while True:
            self.clear()
            self.display_title()

            if not hasattr(self, 'game_mode') or self.game_mode is None:
                self.game_mode = self.select_game_mode()
            if self.game_mode is None:
                continue

            choice = self.display_menu()

            match choice:
                case "1":
                    self.board = Board(rule=self.game_mode)
                    self.play_pvp()
                case "2":
                    self.board = Board(rule=self.game_mode)
                    self.play_vs_ai()
                case "3":
                    self.board = Board(rule=self.game_mode)
                    self.play_ai_vs_ai()
                case "4":
                    self.display_rules()
                case "5":
                    self.load_and_display_game()
                case "6":
                    self.game_mode = None
                case "7":
                    self.clear()
                    print("\nMerci d'avoir joué au Gomoku!\n")
                    break
                case _:
                    print("\nChoix invalide! Veuillez choisir une option entre 1 et 7.")
                    input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    game = GomokuGame()
    game.run()