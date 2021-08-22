# A Sudoku solver in Python

This Sudoku solver implements the method of elimination I use when I play Sudoku, but this only works up to some hard level puzzles. The harder puzzles require some trial and error, so I added backtracking capability to the solver that uses a trial and error approach to solve the harder puzzles.

To run the solver and manually add in the starting grid of a Sudoku puzzle:

```
python3 sudoku_simply.py
```

Alternatively, you can specify one of the puzzle level names that are contained in `sudoku_puzzles.py` with the `-p` parameter, for example:

```
python3 sudoku_simple.py -p expert3

```
