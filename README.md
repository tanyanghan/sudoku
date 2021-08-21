# A Sudoku solver in Python

This Sudoku solver implements the method of elimination I use when I play Sudoku, but this only works up to some hard level puzzles. The harder puzzles require some trial and error, so I added backtracking capability to the solver that uses a trial and error approach to solve the harder puzzles.

To run the solver, you need to specify the puzzle level name that is contained in `sudoku_puzzles.py`, for example:

```
python3 .\sudoku_simple.py -p expert3

```