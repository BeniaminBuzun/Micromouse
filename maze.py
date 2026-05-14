import math
from cell import Cell


class Maze:
    def __init__(self,cell_size):
        self.cell_size = cell_size
        self.maze = set()
        self.first = Cell(0, 0)
        self.maze.add(self.first)

    # north = 0
    # east = 1
    # south = 2
    # west = 3

    #sensors:
    #front = 0
    #left = -1
    #right = 1

    def create_connection(self,cell1,cell2,direction):
        if direction == 0:
            cell1.north = cell2
            cell2.south = cell1
        if direction == 1:
            cell1.east = cell2
            cell2.west = cell1
        if direction == 2:
            cell1.south = cell2
            cell2.north = cell1
        if direction == 3:
            cell1.west = cell2
            cell2.east = cell1

    def update_maze(self,current_cell,facing_direction,sensor_L,sensor_F,sensor_R):
        print(sensor_F)
        print("PPP")
        # add cells in front
        cell_prev = current_cell
        current_direction = facing_direction
        for i in range(math.floor(sensor_F/self.cell_size)):
            new_pos = (cell_prev.pos[0] - current_direction +1 if current_direction%2 == 0 else cell_prev.pos[0], cell_prev.pos[1]+current_direction-2 if current_direction % 2 == 1 else cell_prev.pos[1])
            new_cell = Cell(new_pos[0], new_pos[1])
            self.maze.add(new_cell)
            self.create_connection(cell_prev,new_cell,current_direction)
            cell_prev = new_cell

        # add cells on a left
        cell_prev = current_cell
        current_direction = (facing_direction-1)%4

        for i in range(math.floor(sensor_L/self.cell_size)):
            new_pos = (cell_prev.pos[0] - current_direction +1 if current_direction%2 == 0 else cell_prev.pos[0], cell_prev.pos[1]+current_direction-2 if current_direction % 2 == 1 else cell_prev.pos[1])
            new_cell = Cell(new_pos[0], new_pos[1])
            self.maze.add(new_cell)
            self.create_connection(cell_prev,new_cell,current_direction)
            cell_prev = new_cell

        # add cells on a right
        cell_prev = current_cell
        current_direction = (facing_direction+1)%4

        for i in range(math.floor(sensor_R/self.cell_size)):
            new_pos = (cell_prev.pos[0] - current_direction +1 if current_direction%2 == 0 else cell_prev.pos[0], cell_prev.pos[1]+current_direction-2 if current_direction % 2 == 1 else cell_prev.pos[1])
            new_cell = Cell(new_pos[0], new_pos[1])
            self.maze.add(new_cell)
            self.create_connection(cell_prev,new_cell,current_direction)
            cell_prev = new_cell

        for element in self.maze:
            print(element)