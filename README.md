# Gomoku AI

An alpha-beta search engine for Gomoku, built under a single constraint: pure Python, no external libraries — including for performance-critical parts that would normally reach for C bindings or NumPy.

## The constraint, and what it forces

Python's interpretation overhead makes brute-force search expensive. Without external libraries to offload the hot path to, the only way to make search fast enough is to make the representation itself cheap to manipulate. That constraint shaped every design decision below.

## How it works

**Board representation.** The board is stored as two integers — `position` and `mask` — rather than a grid of cells. `mask` tracks which cells are occupied, `position` tracks which player occupies each one. Testing, setting, or clearing a cell becomes a bitwise operation (AND / XOR / shift) on a machine word instead of an array access, which is where the actual speed comes from.

**Alignment detection.** Winning and near-winning alignments (2, 3, or 4 in a row) are detected per direction — horizontal, vertical, and both diagonals — using precomputed bit offsets rather than scanning the board cell by cell. This is what makes it possible to evaluate a position, and to detect forcing moves, in constant time regardless of board size.

**Search.** Move search runs alpha-beta pruning with a null-window search on top (a narrowed search window used to cheaply confirm or refute a candidate move before committing to a full-width search) and a transposition table keyed directly by the board's bitboard state, so previously evaluated positions are never recomputed.

**Heuristic tuning.** Rather than hand-tuning the weights that drive the evaluation function, `AI_Trainer.py` evolves them with a genetic algorithm: a population of weight sets competes in tournament play, with crossover and three mutation strategies (random, shift, flip) across generations. `bestindividuals.csv` holds the fittest set found so far.

## Structure

| File | Role |
|---|---|
| `board.py` | Bitboard representation, alignment detection |
| `AI.py` | Alpha-beta search, transposition table |
| `AI_Trainer.py` | Genetic algorithm for heuristic weight tuning |
| `game.py` | Game rules and turn logic |
| `Interface_Console.py` | Console interface — the way the engine is actually played |

## Tech stack

Pure Python standard library. No third-party dependencies — a constraint, not an oversight.

## Status

A working engine, playable through the console interface. The genetic algorithm in `AI_Trainer.py` can be re-run to produce a new `bestindividuals.csv`, but doing so is time-intensive by nature — each generation requires full games played out between competing individuals. A graphical interface was started but not completed; the engine itself is fully playable without it.
