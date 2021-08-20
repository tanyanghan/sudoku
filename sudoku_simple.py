import logging, argparse
import tkinter as tk

# import in a sample of Sudoku puzzles of various difficulty levels
from sudoku_puzzles import puzzle

# set up basic logging, if you want to see each cell value being printed out,
# you can set the level to logging.DEBUG
logging.basicConfig(level=logging.INFO, format='%(message)s')

# defines
CTRL_BTN_COL = 9
GO_BTN_ROW = 7
QUIT_BTN_ROW = 0

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
class Sudoku_Cell(tk.Button):
    def __init__(self, master=None, value=0):
        super().__init__(master)
        self.master = master
        if not value:
            self.possible_values = [1,2,3,4,5,6,7,8,9]
            self.config(text="X")
            self.cells_need_updating = False
        else:
            self.possible_values = [value]
            self.config(text=str(value), bg="#34abeb")
            self.cells_need_updating = True
        # create a tooltip that shows the possible values of the cell
        self.tooltip = ToolTip(self)
        self.bind('<Enter>', self.enter_cb)
        self.bind('<Leave>', self.leave_cb)

    def enter_cb(self, event):
        self.tooltip.showtip(str(self.possible_values))

    def leave_cb(self, event):
        self.tooltip.hidetip()
        
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
                # other cells
                self.config(text=str(self.possible_values[0]), 
                            bg="#34abeb")
                self.cells_need_updating = True

    def other_cells_need_updating(self):
        # make a copy of the current status
        current_state = self.cells_need_updating
        # We only need to signal once that cells need to be updated. so we set
        # the status to false here
        self.cells_need_updating = False
        return current_state

    def set_value(self, value):
        self.possible_values = [value]
        self.config(text=str(self.possible_values[0]), 
                    bg="#34abeb")
        self.cells_need_updating = True

    def get_value(self):
        if len(self.possible_values) == 1:
            return self.possible_values[0]
        else:
            return 0

    def get_possible_values(self):
        if  len(self.possible_values) > 1:
            return self.possible_values
        else:
            return []

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
        self.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        self.my_grid=[]
        for row_index in range(9):
            row = []
            tk.Grid.rowconfigure(self, row_index, weight=1)
            for col_index in range(9):
                tk.Grid.columnconfigure(self, col_index, weight=1)
                if seed_values:
                    cell_value = seed_values[row_index][col_index]
                else:
                    cell_value = 0
                cell = cell_class(self, cell_value)
                cell.grid(row=row_index, column=col_index, 
                          sticky=tk.N+tk.S+tk.E+tk.W)
                row.append(cell)
            self.my_grid.append(row)

    def update_grid(self):
        # This function returns True if any cells were updated, and false if
        # no cells were updated. This will let us know when we have gone as
        # far as we can. It also checks if the puzzle has been solved. 

        # we need to keep track if any cells were updated
        updated = False

        # we loop through each cell on the grid
        for i in range(9):
            for j in range(9):
                # we check the cell if it needs other cells updating
                if self.my_grid[i][j].other_cells_need_updating():
                    self.__update_cells(i,j, self.my_grid[i][j].get_value())
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
            possible_values[ROW].append(self.my_grid[row][i].get_possible_values())
            solved_values[ROW].append(self.my_grid[row][i].get_value())
            possible_values[COLUMN].append(self.my_grid[i][column].get_possible_values())
            solved_values[COLUMN].append(self.my_grid[i][column].get_value())

        for i in range(3):
            for j in range(3):
                # here we only update the cells in the correct region
                possible_values[REGION].append(self.my_grid[(qr_off)+i][(qc_off)+j].get_possible_values())
                solved_values[REGION].append(self.my_grid[(qr_off)+i][(qc_off)+j].get_value())

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
                            self.my_grid[row][index].set_value(unique_value)
                        elif i == COLUMN:
                            self.my_grid[index][column].set_value(unique_value)
                        elif i == REGION:
                            self.my_grid[(qr_off)+int(index/3)][(qc_off)+(index-(int(index/3)*3))].set_value(unique_value)

    def is_solved(self):
        # we set the solved status to True here, and we check below for any 
        # cell that doesn't have a value to reset it to false
        self.solved = True
        # we loop through each cell on the grid
        for i in range(9):
            for j in range(9):
                # check every cell for a value, if any cell has no value then
                # the puzzle is still not solved
                if not self.my_grid[i][j].get_value():
                    self.solved = False
        return self.solved

    def __repr__(self):
        string = ""
        for i in range(9):
            for j in range(9):
                string += " %r"%self.my_grid[i][j]
            string += "\n\r"
        return string

    def __str__(self):
        string = ""
        for i in range(9):
            for j in range(9):
                string += "row %d column %d: %s"%(i,j,self.my_grid[i][j])
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

def go_btn_callback():
    if not my_grid.update_grid():
        # once the puzzle has been solved, or if it is unsolvable, hide the 
        # 'Go' button
        go_btn.grid_forget()
    # if logging level set to debug, it will print each cell and the list
    # of possible values
    logging.debug(my_grid)
    # if logging level set to debug or info, it will print the Sudoku grid
    logging.info("%r"%my_grid)

if __name__ == "__main__":
    # get the chosen puzzle difficulty level
    args = parseOptions()

    root = tk.Tk()
    root.title('Sudoku')
    root.geometry('660x540')
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 0, weight=1)

    # instantiate a Sudoku grid with seed values
    my_grid = Sudoku_Grid(root, puzzle[args.puzzle_level])

    # configure a column for the control buttons
    tk.Grid.columnconfigure(my_grid, CTRL_BTN_COL, weight=2)

    # instantiate a 'Go' control button
    go_btn = tk.Button(my_grid, text='Go', bg="#3deb34",
                           command=go_btn_callback)

    # add the 'Go' button to the control button column
    go_btn.grid(row=GO_BTN_ROW, column=CTRL_BTN_COL, rowspan=2 ,
                    sticky=tk.N+tk.S+tk.E+tk.W)

    # instantiate a 'Quit' control button
    quit_btn = tk.Button(my_grid, text="QUIT", bg="red",
                             command=root.quit)

    # add the 'Quit' button to the control button column
    quit_btn.grid(row=QUIT_BTN_ROW, column=CTRL_BTN_COL, 
                      sticky=tk.N+tk.S+tk.E+tk.W)

    root.mainloop()

    # after we exit the loop above, we check if the puzzle has been solved
    my_grid.update_grid()
    if not my_grid.is_solved():
        logging.info("Puzzle not solved")
    else:
        logging.info("Puzzle solved!")

    root.destroy()
