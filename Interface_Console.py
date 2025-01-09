import os
import random
from typing import Tuple, Optional
from datetime import datetime
from pyfiglet import Figlet
from board import Board
from AI import AI

#Liste des derniers coups joués par les joueurs

class GomokuGame:
    def __init__(self):
        self.board = Board()
        self.ai = AI(self.board)
        self.game_mode = "normal"
        self.style_x = "\033[91mX\033[0m"
        self.style_o = "\033[94mO\033[0m"
        self.move_player_1 = []
        self.move_player_2 = []

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_title(self):
        print(Figlet(font='slant').renderText('Gomoku'))

    def display_menu(self) -> str:
        print("\n" + "═" * 50)
        print("Menu Principal:")
        print("1. Joueur contre Joueur")
        print("2. Joueur contre IA")
        print("3. Règles du jeu")
        print("4. Quitter")
        print("═" * 50)
        return input("\nVotre choix (1-4): ")

    def select_game_mode(self) -> str:
        self.clear()
        self.display_title()
        print("\n" + "═" * 50)
        print("Sélection du mode de jeu:")
        print("1. Mode Normal")
        print("2. Mode Pro ")
        print("═" * 50)

        while True:
            choice = input("\nVotre choix (1-2): ")
            if choice == "1":
                return "normal"
            elif choice == "2":
                return "pro"
            else:
                print("Choix invalide! Veuillez choisir 1 ou 2.")

    def select_first_player(self, vs_ai: bool = False) -> int:
        self.clear()
        print("\n" + "═" * 50)
        print("Qui commence la partie ?")
        if vs_ai:
            print("1. Joueur")
            print("2. IA")
        else:
            print(f"1. Joueur 1 ({self.style_o})")
            print(f"2. Joueur 2 ({self.style_x})")
        print("3. Aléatoire")
        print("═" * 50)

        while True:
            choice = input("\nVotre choix (1-3): ")
            if choice in ["1", "2"]:
                return int(choice)
            elif choice == "3":
                first = random.randint(1, 2)
                if vs_ai:
                    if first == 1:
                        print("\nLe joueur commence!")
                    else:
                        print("\nL'IA commence!")
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

        if self.game_mode == "pro":
            rules_text += """
        Règles additionnelles du mode Pro:
        • BLABLABLA
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
                self.board.clean_move(move)
                if move not in self.board.can_play:
                    print("Cette case est déjà prise!")
                    continue
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
        if game_mode == "Joueur contre IA" and current_player == 2:
            print("Tour de l'IA....")
        print(self.board)

    def play_pvp(self):
        current_player = self.select_first_player(vs_ai=False)
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
                input("\nAppuyez sur Entrée pour revenir au menu...")
                break

            current_player = 3 - current_player

    def play_vs_ai(self):
        current_player = self.select_first_player(vs_ai=True)
        value_board = 0
        game_mode = "Joueur contre IA"

        while True:
            self.display_game_state(current_player, game_mode)

            if current_player == 1:
                move = self.get_player_move(current_player)
                if move.lower() == 'quit':
                    break
            else:
                _, move, _ = self.ai.search(self.board, current_player, value_board)
                if move is None:
                    print("L'IA n'a pas pu trouver de coup valide!")
                    break
                print(f"\nL'IA joue: {move}")

            self.board.play_to(current_player, move)
            value_board = self.board.heuristic(value_board, move, current_player)

            winner = self.board.is_winning
            if winner is not None:
                self.display_game_state(current_player, game_mode)
                if winner == 0:
                    print("\n═══ Match nul! ═══")
                elif winner == 1:
                    print("\n═══ Vous avez gagné contre l'IA! ═══")
                else:
                    print("\n═══ L'IA vous a écrasé! ═══")

                input("\nAppuyez sur Entrée pour revenir au menu...")
                break

            current_player = 3 - current_player

    def run(self):
        while True:
            self.clear()
            self.display_title()

            if not hasattr(self, 'game_mode'):
                self.game_mode = self.select_game_mode()

            choice = self.display_menu()

            match choice:
                case "1":
                    self.board = Board()
                    self.play_pvp()
                case "2":
                    self.board = Board()
                    self.play_vs_ai()
                case "3":
                    self.display_rules()
                case "4":
                    self.clear()
                    print("\nMerci d'avoir joué au Gomoku!\n")
                    break
                case _:
                    print("\nChoix invalide! Veuillez choisir une option entre 1 et 4.")
                    input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    game = GomokuGame()
    game.run()