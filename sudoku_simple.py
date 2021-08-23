import logging, argparse, copy, json
import tkinter as tk
from tkinter import font as tkFont

# import in a sample of Sudoku puzzles of various difficulty levels
from sudoku_puzzles import puzzle

# set up basic logging, if you want to see each cell value being printed out,
# you can set the level to logging.DEBUG
logging.basicConfig(level=logging.INFO, format='%(message)s')

# defines
CTRL_BTN_COL    = 9
QUIT_BTN_ROW    = 0
CLEAR_BTN_ROW   = 1
REVERT_BTN_ROW  = 3
TRY_BTN_ROW     = 5
GO_BTN_ROW      = 7

CELL_FILLED_COLOUR = "#34abeb"

GRID_DIMENSION  = 60
CTRL_COLUMNSPAN = 2
NUM_COLUMNS     = (9+CTRL_COLUMNSPAN)
NUM_ROWS        = 9
WINDOW_WIDTH    = (GRID_DIMENSION * NUM_COLUMNS)
WINDOW_HEIGHT   = (GRID_DIMENSION * NUM_ROWS)

# This class displays a tooltip showing the possible values of a cell as the
# mouse hovers over the cell grid
class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def showtip(self, text):
        self.text = text
        if self.tipwindow or not self.text:
            logging.debug("returning")
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        try:
            # For Mac OS
            tw.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", tw._w,
                       "help", "noActivates")
        except tk.TclError:
            pass
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=("tahoma", "14", "normal"))
        label.pack(ipadx=1)
        tw.update_idletasks()  # Needed on MacOS -- see #34275.
        tw.lift()  # work around bug in Tk 8.5.18+ (issue #24570)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# This class defines a single cell on a Sudoku grid
class Sudoku_Cell(tk.Entry):
    def __init__(self, master=None, value=0):
        super().__init__(master)
        self.master = master
        # save the default background colour for use later
        self.original_bg = self.cget("bg")
        self.cell_string = tk.StringVar()
        # set the font for the number grid
        self.config(font=grid_font, textvariable=self.cell_string, justify="center", 
                    disabledbackground="#d3d3d3", disabledforeground="blue")
        self.bind("<KeyRelease>", self.entry_change) #keyup  
        if not value:
            # no value given for this cell, initialize to all possible_values
            self.possible_values = [1,2,3,4,5,6,7,8,9]
            self.cell_string.set("")
            self.cells_need_updating = False
        else:
            if isinstance(value, list):
                # if value is a list, assume it's the list of possible_values
                self.possible_values = value
            else:
                # assign the given value as the value of this cell
                self.possible_values = [value]
                self.config(state='disabled')
            # check if the cell has been set to a value
            self.__check_value_set()
        # create a tooltip that shows the possible values of the cell
        self.tooltip = ToolTip(self)
        self.bind('<Enter>', self.enter_cb)
        self.bind('<Leave>', self.leave_cb)

    def enter_cb(self, event):
        self.tooltip.showtip(str(self.possible_values))

    def leave_cb(self, event):
        self.tooltip.hidetip()

    def entry_change(self, event):
        try:
            value = int(self.cell_string.get()[0])
        except (ValueError, IndexError):
            self.cell_string.set("")
            self.possible_values = [1,2,3,4,5,6,7,8,9]
            self.config(bg=self.original_bg)
        else:
            if value > 0 and value < 10:
                self.set_state(value)
        finally:
            self.master.focus()
        
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
            self.__check_value_set()

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

    def get_possible_values(self):
        return self.possible_values

    def set_state(self, possible_values):
        if isinstance(possible_values, list):
            self.possible_values = possible_values
        else:
            if not possible_values:
                self.possible_values = [1,2,3,4,5,6,7,8,9]
            else:
                self.possible_values = [possible_values]
        self.cells_need_updating = False
        self.cell_string.set("")
        self.config(bg=self.original_bg, state="normal")
        self.__check_value_set()

    def set_error(self):
        self.config(bg="red")

    def __check_value_set(self):
        if len(self.possible_values) == 1:
            # cell value has been determined, flag that we need to update
            # other cells
            self.cell_string.set(str(self.possible_values[0]))
            self.config(bg=CELL_FILLED_COLOUR)
            self.cells_need_updating = True

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
class Sudoku_Grid(tk.Frame):
    def __init__(self, master=None, seed_values=[], cell_class=Sudoku_Cell):
        super().__init__(master)
        self.master = master
        self.solved = False
        self.my_grid=[]
        for row_index in range(9):
            row = []
            self.master.rowconfigure(row_index, weight=1)
            for col_index in range(9):
                self.master.columnconfigure(col_index, weight=1)
                if seed_values:
                    cell_value = seed_values[row_index][col_index]
                else:
                    cell_value = 0
                cell = cell_class(self.master, cell_value)
                cell.grid(row=row_index, column=col_index, 
                          sticky=tk.N+tk.S+tk.E+tk.W)
                row.append(cell)
            self.my_grid.append(row)

    def reset_grid(self, seed_values):
        # this function will take the output from Sudoku_Grid.get_state() as 
        # the 'seed_values' parameter, and reset the state of the grid 
        for (grid_row, seed_row) in zip(self.my_grid, seed_values):
            for cell, seed_value in zip(grid_row, seed_row):
                cell.set_state(seed_value)

    def update_grid(self):
        # This function returns True if any cells were updated, and false if
        # no cells were updated. This will let us know when we have gone as
        # far as we can. It also checks if the puzzle has been solved. 

        # we need to keep track if any cells were updated
        updated = False

        # we loop through each cell on the grid
        for row in self.my_grid:
            for cell in row: 
                # we check the cell if it needs other cells updating
                if cell.other_cells_need_updating():
                    self.__update_cells(self.my_grid.index(row),row.index(cell),cell.get_value())
                    # update the status that a cell was updated
                    updated = True

        # check through each row/column/region for unique values
        for row in range(9):
            self.__check_unique(row,int((row*12)%9+(row/3)))

        # check if the puzzle has been solved
        self.is_solved()

        # We return the status whether any cells were updated.
        # We do this as long as the puzzle has not been solved. Once the puzzle
        # has been solved, we return false to break the loop.
        return updated and not self.solved

    def __update_cells(self,row,column,value):
        # This function loops through each cell on a corresponding row, column
        # and region to remove the value from each cells' possible value list

        # we update the corresponding row and column together in a single loop
        for i in range(9):
            if (i != column and self.my_grid[row][i].get_value() == value):
                self.my_grid[row][column].set_error()
                self.my_grid[row][i].set_error()
                raise AttributeError("Invalid cell (%d,%d) value %d"%(row,column,value))
            if (i != row and self.my_grid[i][column].get_value() == value):
                self.my_grid[row][column].set_error()
                self.my_grid[i][column].set_error()
                raise AttributeError("Invalid cell (%d,%d) value: %d"%(row,column,value))
            self.my_grid[row][i].remove_possible_value(value)
            self.my_grid[i][column].remove_possible_value(value)

        # to update the region, we'll need to calculate an offset to the
        # start of the region
        qr_off = int(row/3)*3
        qc_off = int(column/3)*3

        # now we'll loop through the 3x3 region
        for i in range(3):
            for j in range(3):
                # here we only update the cells in the correct region
                if ( (row != (qr_off)+i and column != (qc_off)+j) and 
                     (self.my_grid[(qr_off)+i][(qc_off)+j].get_value() == value)
                   ):
                    self.my_grid[row][column].set_error()
                    self.my_grid[(qr_off)+i][(qc_off)+j].set_error()
                    raise AttributeError("Invalid cell (%d,%d) value: %d"%(row,column,value))
                self.my_grid[(qr_off)+i][(qc_off)+j].remove_possible_value(value)

    def __check_unique(self,row,column):
        # to update the region, we'll need to calculate an offset to the
        # start of the region
        qr_off = int(row/3)*3
        qc_off = int(column/3)*3

        # after we updated all the cells, we go through them again to see if
        # each cell has a unique possible value
        ROW = 0
        COLUMN = 1
        REGION = 2
        possible_values = [[],[],[]]
        solved_values = [[],[],[]]
        for i in range(9):
            cell_value = self.my_grid[row][i].get_value()
            if cell_value:
                solved_values[ROW].append(cell_value)
                # append an empty list to the possible_values[], as we need the
                # index to match
                possible_values[ROW].append([])
            else:
                possible_values[ROW].append(self.my_grid[row][i].get_possible_values())

            cell_value = self.my_grid[i][column].get_value()
            if cell_value:
                solved_values[COLUMN].append(cell_value)
                # append an empty list to the possible_values[], as we need the
                # index to match
                possible_values[COLUMN].append([])
            else:
                possible_values[COLUMN].append(self.my_grid[i][column].get_possible_values())

        for i in range(3):
            for j in range(3):
                # here we only update the cells in the correct region
                cell_value = self.my_grid[(qr_off)+i][(qc_off)+j].get_value()
                if cell_value:
                    solved_values[REGION].append(cell_value)
                    # append an empty list to the possible_values[], as we need
                    # the index to match
                    possible_values[REGION].append([])
                else:
                    possible_values[REGION].append(self.my_grid[(qr_off)+i][(qc_off)+j].get_possible_values())

        # find the unique values
        unique_values = [[],[],[]]
        for i in range(3):
            all_possible_values = []
            for values in possible_values[i]:
                all_possible_values = all_possible_values + values
            for possible_value in all_possible_values:
                if all_possible_values.count(possible_value) == 1 and possible_value not in solved_values[i]:
                    unique_values[i].append(possible_value)

        # check if any unique values exist
        for i in range(3):
            for unique_value in unique_values[i]:
                for values in possible_values[i]:
                    if unique_value in values:
                        index = possible_values[i].index(values)
                        if i == ROW:
                            self.my_grid[row][index].set_state(unique_value)
                        elif i == COLUMN:
                            self.my_grid[index][column].set_state(unique_value)
                        elif i == REGION:
                            self.my_grid[(qr_off)+int(index/3)][(qc_off)+(index-(int(index/3)*3))].set_state(unique_value)

    def is_solved(self):
        # we set the solved status to True here, and we check below for any 
        # cell that doesn't have a value to reset it to false
        self.solved = True
        # we loop through each cell on the grid
        for row in self.my_grid:
            for cell in row:               
                # check every cell for a value, if any cell has no value then
                # the puzzle is still not solved
                if not cell.get_value():
                    self.solved = False
        return self.solved

    def try_next(self, try_number=0):
        # This function searches for a cell with 2 possible values, and sets
        # the cell value to one of the two possible values. The parameter
        # try_number determines which of the two possible values is used.
        # It returns True if it successfully sets a cell, or returns False if
        # it did not manage to set a cell.
        for row in self.my_grid:
            for cell in row:
                possible_values = cell.get_possible_values()
                if len(possible_values) == 2:
                    cell.set_state(possible_values[try_number])
                    logging.info("Trying cell (%d,%d) value %d from %s"%
                        (self.my_grid.index(row),row.index(cell),possible_values[try_number],possible_values))
                    return True
        return False

    def get_state(self):
        # get_state returns the current state of the grid as a list of possible
        # value
        state = []
        for row in self.my_grid:
            row_values = []
            for cell in row:
                row_values.append(cell.get_possible_values())
            state.append(row_values)
        return state

    def __repr__(self):
        string = ""
        for row in self.my_grid:
            for cell in row:
                string += " %r"%cell
            string += "\n\r"
        return string

    def __str__(self):
        string = ""
        for row in self.my_grid:
            for cell in row:
                string += "row %d column %d: %s"%(self.my_grid.index(row),row.index(cell),cell)
                string += "\n\r"
        return string

def go_btn_callback():
    try:
        if not my_grid.update_grid():
            # once the puzzle has been solved, or if it is unsolvable, hide the 
            # 'Go' button
            go_btn.grid_remove()
            if not my_grid.is_solved():
                # add the 'Try' button to the control button column
                try_btn.grid()
            else:
                # show the 'Clear' button because the puzzle is unsolvable
                clear_btn.grid()
    except AttributeError as e:
        # An AttributeError here means that a cell value clash has occurred.
        # Hide the 'Go' button
        go_btn.grid_remove()

        # If the grid stack is not empty, it means we can revert to a prior
        # grid state.
        if grid_stack:
            # Show the 'Revert' button to allow the user to revert to a prior
            # grid state
            revert_btn.grid()
        # we log the clash cell coordinate and the value
        logging.error(str(e))

    # if logging level set to debug, it will print each cell and the list
    # of possible values
    logging.debug(my_grid)
    # if logging level set to debug or info, it will print the Sudoku grid
    logging.debug("%r"%my_grid)

def try_btn_callback():
    # first we make a copy of the grid as it is and push it onto the stack
    grid_stack.append({'grid':copy.deepcopy(my_grid.get_state()), 'try_number':0})
    # next we tell the grid to try the first possibility of a cell with only
    # two possibilities
    result = my_grid.try_next(0)

    # hide the try button
    try_btn.grid_remove()

    if result:
        # add the 'Go' button to the control button column
        go_btn.grid()
    else:
        # show the 'Clear' button because the puzzle is unsolvable
        clear_btn.grid()

def revert_btn_callback():
    result = False
    # we pop the grids that we have already tried both possibilities, off the
    # stack
    while grid_stack and grid_stack[-1]['try_number'] == 1:
        grid_stack.pop()
    # if the grid stack is not empty, we try the second possibility of the last
    # grid on the stack
    if grid_stack:
        grid_stack[-1]['try_number'] = 1
        my_grid.reset_grid(grid_stack[-1]['grid'])
        result = my_grid.try_next(1)

    # hide the revert button
    revert_btn.grid_remove()

    if result:
        # add the 'Go' button to the control button column
        go_btn.grid()
    else:
        # show the 'Clear' button because the puzzle is unsolvable
        clear_btn.grid()

def clear_btn_callback():
    # clear the grid stack
    grid_stack = []

    # reset the grid to empty
    my_grid.reset_grid(puzzle['empty'])

    # hide the 'Clear' button
    clear_btn.grid_remove()

    # add the 'Go' button to the control button column
    go_btn.grid()

def parseOptions():
    parser = argparse.ArgumentParser(description="A simple Sudoku puzzle solver")

    parser.add_argument("-p", "--puzzle_level", 
        help="Selects the difficulty level of the puzzle",
        choices=puzzle.keys(),
        action="store", required=False, default="empty")

    args = parser.parse_args()

    return args

if __name__ == "__main__":
    # declare a stack to hold grid information for "tries"
    grid_stack = []

    # get the chosen puzzle difficulty level
    args = parseOptions()

    root = tk.Tk()
    root.title('Sudoku')
    root.geometry('%dx%d'%(WINDOW_WIDTH, WINDOW_HEIGHT))

    grid_font = tkFont.Font(family='Helvetica',size=24, weight='bold')
    control_font = tkFont.Font(family='Helvetica',size=18, weight='bold')

    # instantiate a Sudoku grid with seed values
    my_grid = Sudoku_Grid(root, puzzle[args.puzzle_level])

    # configure a column for the control buttons
    root.columnconfigure(CTRL_BTN_COL, weight=0, minsize=GRID_DIMENSION*CTRL_COLUMNSPAN)

    # instantiate a 'Go' control button
    go_btn = tk.Button(root, text='Go', bg="#3deb34",
                           font=control_font, command=go_btn_callback)

    # add the 'Go' button to the control button column
    go_btn.grid(row=GO_BTN_ROW, column=CTRL_BTN_COL, rowspan=2,
                    sticky=tk.N+tk.S+tk.E+tk.W)

    # instantiate a 'Quit' control button
    quit_btn = tk.Button(root, text="QUIT", bg="red",
                             font=control_font, command=root.quit)

    # add the 'Quit' button to the control button column
    quit_btn.grid(row=QUIT_BTN_ROW, column=CTRL_BTN_COL, 
                      sticky=tk.N+tk.S+tk.E+tk.W)

    # instantiate a 'Try' control button
    try_btn = tk.Button(root, text='Try', bg="#ffa500",
                           font=control_font, command=try_btn_callback)

    # add the 'Try' button to the control button column
    try_btn.grid(row=TRY_BTN_ROW, column=CTRL_BTN_COL, rowspan=2,
                    sticky=tk.N+tk.S+tk.E+tk.W)

    # instantiate a 'Revert' control button
    revert_btn = tk.Button(root, text='Revert', bg="#ffff00",
                           font=control_font, command=revert_btn_callback)

    # add the 'Revert' button to the control button column
    revert_btn.grid(row=REVERT_BTN_ROW, column=CTRL_BTN_COL, rowspan=2,
                        sticky=tk.N+tk.S+tk.E+tk.W)

    # instantiate a 'Clear' control button
    clear_btn = tk.Button(root, text='Clear', bg="#ff00ff",
                           font=control_font, command=clear_btn_callback)

    # add the 'Clear' button to the control button column
    clear_btn.grid(row=CLEAR_BTN_ROW, column=CTRL_BTN_COL, rowspan=2,
                        sticky=tk.N+tk.S+tk.E+tk.W)

    # hide the 'Try', 'Revert' and 'Clear' buttons
    try_btn.grid_remove()
    revert_btn.grid_remove()
    clear_btn.grid_remove()

    root.mainloop()

    # after we exit the loop above, we check if the puzzle has been solved
    my_grid.update_grid()
    if not my_grid.is_solved():
        logging.info("Puzzle not solved")
    else:
        logging.info("Puzzle solved!")

    root.destroy()
