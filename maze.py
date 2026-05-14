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

    def calculate_direction(self,current_cell,facing_direction,sensor_direction):
        direction = (facing_direction + sensor_direction )%4
        if direction == 0:
            return current_cell.north
        if direction == 1:
            return current_cell.east
        if direction == 2:
            return current_cell.south
        if direction == 3:
            return current_cell.west
        
    def update_maze(self,current_cell,facing_direction,sensor_L,sensor_F,sensor_R):
        print(sensor_F)
        cell_R = current_cell
        for i in range(math.floor(sensor_F/self.cell_size)):
            new_cell = Cell(cell_R.pos[0]+1,cell_R.pos[1])
            self.maze.add(new_cell)
            connection = self.calculate_direction(current_cell,facing_direction,0)
            connection = new_cell
            connection2 = self.calculate_direction(new_cell,facing_direction+2,0)
            connection2 = cell_R
            cell_R = new_cell
            print("A")
#             for i in range(math.floor(sensor_R/self.cell_size)):
#                 print("B")
#             for i in range(math.floor(sensor_L/self.cell_size)):
#                 print("C")
        for element in self.maze:
            print(element)