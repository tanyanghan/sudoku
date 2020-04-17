import logging, argparse

# import in a sample of Sudoku puzzles of various difficulty levels
from sudoku_puzzles import puzzle

# set up basic logging, if you want to see each cell value being printed out,
# you can set the level to logging.DEBUG
logging.basicConfig(level=logging.INFO, format='%(message)s')

# This class defines a single cell on a Sudoku grid
class Sudoku_Cell:
    def __init__(self, value=0):
        if not value:
            self.possible_values = [1,2,3,4,5,6,7,8,9]
            self.cells_need_updating = False
        else:
            self.possible_values = [value]
            self.cells_need_updating = True
        
    def remove_possible_value(self,value):
        if len(self.possible_values) == 1:
            # we have already arrived at an answer previously, do nothing
            return

        try:
            self.possible_values.remove(value)
        except ValueError:
            # value not found, continue
            pass
        else:
            # value removed, check if we have arrived at an answer
            if len(self.possible_values) == 1:
                # cell value has been determined, flag that we need to update
                #other cells
                self.cells_need_updating = True

    def other_cells_need_updating(self):
        # make a copy of the current status
        current_state = self.cells_need_updating
        # We only need to signal once that cells need to be updated. so we set
        # the status to false here
        self.cells_need_updating = False
        return current_state

    def get_value(self):
        if len(self.possible_values) == 1:
            return self.possible_values[0]
        else:
            return 0

    def __repr__(self):
        if len(self.possible_values) == 1:
            return "%d"%self.possible_values[0]
        else:
            return "X"

    def __str__(self):
        if len(self.possible_values) == 1:
            return "%d"%(self.possible_values[0])
        else:
            return "X (Possible values: %s)"%(self.possible_values) 

# This class takes a 9x9 2-dimensional array of numbers that represents the
# starting grid of a Sudoku puzzle. A value of 0 represents an unfilled cell.
class Sudoku_Grid:
    def __init__(self,seed_values=[], cell_class=Sudoku_Cell):
        self.solved = False
        self.grid=[]
        for i in range(9):
            row = []
            for j in range(9):
                if seed_values:
                    cell_value = seed_values[i][j]
                else:
                    cell_value = 0
                row.append(cell_class(cell_value))
            self.grid.append(row)

    def update_grid(self):
        # This function returns True if any cells were updated, and false if
        # no cells were updated. This will let us know when we have gone as
        # far as we can. It also checks if the puzzle has been solved. 

        # we need to keep track if any cells were updated
        updated = False

        # we set the solved status to True here, and we check below for any 
        # cell that doesn't have a value to reset it to false
        self.solved = True

        # we loop through each cell on the grid
        for i in range(9):
            for j in range(9):
                # we check the cell if it needs other cells updating
                if self.grid[i][j].other_cells_need_updating():
                    self.__update_cells(i,j, self.grid[i][j].get_value())
                    # update the status that a cell was updated
                    updated = True
                # check every cell for a value, if any cell has no value then
                # the puzzle is still not solved
                if not self.grid[i][j].get_value():
                    self.solved = False

        # We return the status whether any cells were updated.
        # We do this as long as the puzzle has not been solved. Once the puzzle
        # has been solved, we return false to break the loop.
        return updated and not self.solved

    def __update_cells(self,row,column,value):
        # This function loops through each cell on a corresponding row, column
        # and region to remove the value from each cells' possible value list

        # we update the corresponding row and column together in a single loop
        for i in range(9):
            self.grid[row][i].remove_possible_value(value)
            self.grid[i][column].remove_possible_value(value)

        # to update the region, we'll need to calculate an offset to the
        # start of the region
        qr_off = int(row/3)*3
        qc_off = int(column/3)*3

        # now we'll loop through the 3x3 region
        for i in range(3):
            for j in range(3):
                # here we only update the cells in the correct region
                self.grid[(qr_off)+i][(qc_off)+j].remove_possible_value(value)

    def is_solved(self):
        return self.solved

    def __repr__(self):
        string = ""
        for i in range(9):
            for j in range(9):
                string += " %r"%self.grid[i][j]
            string += "\n\r"
        return string

    def __str__(self):
        string = ""
        for i in range(9):
            for j in range(9):
                string += "row %d column %d: %s"%(i,j,self.grid[i][j])
                string += "\n\r"
        return string

def parseOptions():
    parser = argparse.ArgumentParser(description="A simple Sudoku puzzle solver")

    parser.add_argument("-p", "--puzzle_level", 
        help="Selects the difficulty level of the puzzle",
        choices=puzzle.keys(),
        action="store", required=True)

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    # get the chosen puzzle difficulty level
    args = parseOptions()

    # instantiate a Sudoku grid with seed values
    my_grid = Sudoku_Grid(puzzle[args.puzzle_level])

    # here is our main loop that calls update_grid until it cannot proceed
    # further, or the puzzle is solved
    while my_grid.update_grid():
        # if logging level set to debug, it will print each cell and the list
        # of possible values
        logging.debug(my_grid)
        # if logging level set to debug or info, it will print the Sudoku grid
        logging.info("%r"%my_grid)
        # wait for user to press enter
        input("Press Enter to continue...")

    # after we exit the loop above, we check if the puzzle has been solved
    if not my_grid.is_solved():
        logging.info("Puzzle unsolvable")
    else:
        logging.info("Puzzle solved!")
