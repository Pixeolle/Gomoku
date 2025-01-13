import random
import numpy as np
from typing import *
from board import Board
from AI import AI
import math
from multiprocessing import Pool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AI_Trainer:
    def __init__(self, population_size = 8, mutation_rate = 0.01, selection_size = 4, start_population = "bestindividuals.csv", rule = "long pro", time_to_play = 0.5):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.selection_size = selection_size
        self.start_population = start_population
        self.rule = rule
        self.time_to_play = time_to_play


    def train(self, generation : int):
        population = self.initialize_population(self.read_csv("bestindividuals.csv"))
        for i in range(generation):
            population = self.tournament(population)
            print(f"Generation {i} : {population}")
            population = self.recreate_population(population)
        best_individuals = self.tournament(population)
        self.best_individuals(best_individuals, "bestindividuals.csv")

    def match(self, individual1: Dict, individual2: Dict) -> Dict:
        score = [0, 0]
        match_count = 1

        while max(score) < 2 and match_count < 4:
            board = Board(rule=self.rule)
            ai1 = AI(board, self.time_to_play)
            ai2 = AI(board, self.time_to_play)


            last_move = None
            if match_count == 1:
                player = 1
            elif match_count == 2:
                player = 2
            else:
                player = 1 if random.random() > 0.5 else 2

            moves_without_valid = 0
            max_invalid_moves = 3

            while board.is_winning is None:
                try:
                    current_ai = ai1 if player == 1 else ai2
                    _, move, _ = current_ai.search(board, player, last_move)

                    # Handle invalid or None moves
                    if move is None or not self.is_valid_move(board, move):
                        moves_without_valid += 1
                        logger.warning(f"Invalid move from player {player}: {move}")

                        if moves_without_valid >= max_invalid_moves:
                            logger.error(f"Too many invalid moves from player {player}")
                            return individual2 if player == 1 else individual1

                        # Generate a random valid move as fallback
                        valid_moves = board.can_play
                        if valid_moves:
                            move = random.choice(valid_moves)
                            logger.info(f"Generated random move: {move}")
                        else:
                            logger.error("No valid moves available")
                            break
                    else:
                        moves_without_valid = 0  # Reset counter on valid move

                    board.play_to(player, move)
                    last_move = move
                    player ^= 3  # Switch players (1->2 or 2->1)

                except Exception as e:
                    logger.error(f"Error during game: {str(e)}")
                    return individual2 if player == 1 else individual1

            # Record match result
            if board.is_winning == 1:
                score[0] += 1
            elif board.is_winning == 2:
                score[1] += 1

            match_count += 1

        return individual1 if score[0] >= score[1] else individual2

    def is_valid_move(self, board: Board, move: str) -> bool:
        """Validate if a move is legal on the current board."""
        try:
            if move is None:
                return False
            if not isinstance(move, str):
                return False
            if move not in board.can_play:
                return False
            _, line, column = board.clean_move(move)
            return True
        except (ValueError, AttributeError):
            return False

    def tournament(self, population: List[Dict]) -> List[Dict]:
        with Pool() as pool:
            while len(population) > self.selection_size:
                # Create pairs for matches
                pairs = [(population[i], population[i + 1])
                         for i in range(0, len(population), 2)]

                try:
                    results = pool.starmap(self.match, pairs)
                    population = [r for r in results if r is not None]

                    # Handle case where all matches failed
                    if not population:
                        logger.error("All tournament matches failed")
                        return population[:self.selection_size]

                except Exception as e:
                    logger.error(f"Tournament error: {str(e)}")
                    # Return surviving population if tournament fails
                    return population[:self.selection_size]

        return population



    def read_csv(self, pathfile : str) -> List[Dict]:
        try :
            with open(pathfile, "r") as file:
                if file.readline() == "":
                    return []
                return [{int(key) : int(value) for key, value in line.strip().split(",")} for line in file]
        except FileNotFoundError:
            return []

    def best_individuals(self, population : List[Dict], pathfile : str) -> None:
        with open(pathfile, "w") as file:
            for individual in population:
                file.write(",".join(str(value) for value in individual.values()) + "\n")

    def initialize_population(self, original : List[Dict]) -> List[Dict]:
        if len(original) > self.population_size:
            raise ValueError("The original population is bigger than the population size")

        population = original.copy()
        while len(population) < self.population_size:
            population.append(self.random_individual())

        return population

    def recreate_population(self, population : List[Dict]) -> List[Dict]:
        new_population = []
        while len(new_population) < self.population_size:
            parent1, parent2 = random.choices(population, k = 2)
            new_population.append(self.mutate(self.cross(parent1, parent2)))
        for _ in range(math.floor(self.population_size * self.mutation_rate)):
            new_population[random.randint(0, self.population_size - 1)] = self.mutate(random.choice(population))
        return new_population


    def cross(self, parent1 : Dict, parent2 : Dict) -> Dict:
        child = {}
        for key in parent1:
            child[key] = parent1[key] if random.random() > 0.5 else parent2[key]
        return child

    def mutate(self, individual : Dict) -> Dict:
        rd_choice = random.randint(1,3)
        if rd_choice == 1:
            return self.mutate_random(individual)
        elif rd_choice == 2:
            return self.mutate_shift(individual)
        else:
            return self.mutate_flip(individual)

    def mutate_random(self, individual : Dict) -> Dict:
        for key in individual:
            if random.random() < self.mutation_rate:
                individual[key] = random.randint(0, 10000)
        return individual

    def mutate_shift(self, individual : Dict) -> Dict:
        for key in individual:
            if random.random() < self.mutation_rate:
                individual[key] += random.randint(-100, 100)
        return individual

    def mutate_flip(self, individual : Dict) -> Dict:
        for key in individual:
            if random.random() < self.mutation_rate:
                individual[key] = 10000 - individual[key]
        return individual

    def random_individual(self) -> Dict:
        weights = {}
        for i in range(2,5):
            weights[i] = random.randint(0, 10000)
        weights[5] = 10000
        return weights


if __name__ == "__main__":
    aitrain = AI_Trainer()
    aitrain.train(10)

