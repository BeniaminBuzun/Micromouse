import math
from cell import Cell


class Maze:
    def __init__(self,cell_size):
        self.cell_size = cell_size
        self.maze = {}
        self.first = Cell(0, 0)
        self.maze["0,0"] = self.first

    # north = 0
    # east = 1
    # south = 2
    # west = 3

    #sensors:
    #front = 0
    #left = -1
    #right = 1
    def get_wall_distance(self, cell, direction):
        if direction == 0:  # north
            return self.cell_size+self.get_wall_distance(cell.north, direction) if cell.north else self.cell_size/2
        elif direction == 1:  # east
            return self.cell_size+self.get_wall_distance(cell.east, direction) if cell.east else self.cell_size/2   
        elif direction == 2:  # south
            return self.cell_size+self.get_wall_distance(cell.south, direction) if cell.south else self.cell_size/2
        elif direction == 3:  # west
            return self.cell_size+self.get_wall_distance(cell.west, direction) if cell.west else self.cell_size/2           
             
    def get_current_cell(self, cellX, cellY):
        return self.maze.get(f"{cellX},{cellY}")


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
    def get_or_create_neighbor(self, cell, direction):
        """Get existing neighbor cell or create a new one if it doesn't exist"""
        # Check if neighbor already exists
        if direction == 0:  # north
            if cell.north:
                return cell.north
        elif direction == 1:  # east
            if cell.east:
                return cell.east
        elif direction == 2:  # south
            if cell.south:
                return cell.south
        elif direction == 3:  # west
            if cell.west:
                return cell.west
        
        # Create new cell if it doesn't exist
        new_pos = (cell.pos[0] + direction - 2 if direction % 2 == 1 else cell.pos[0],
                   cell.pos[1] - direction + 1 if direction % 2 == 0 else cell.pos[1])
        new_cell = Cell(new_pos[0], new_pos[1])
        self.maze[f"{new_pos[0]},{new_pos[1]}"] = new_cell
        self.create_connection(cell, new_cell, direction)
        return new_cell

    def update_maze(self,current_cell,facing_direction,sensor_L,sensor_F,sensor_R):
        print(sensor_F)
        print("PPP")
        # add cells in front
        cell_prev = current_cell
        current_direction = facing_direction
        for i in range(math.floor(sensor_F/self.cell_size)):
            cell_prev = self.get_or_create_neighbor(cell_prev, current_direction)

        # add cells on a left
        cell_prev = current_cell
        current_direction = (facing_direction-1)%4

        for i in range(math.floor(sensor_L/self.cell_size)):
            cell_prev = self.get_or_create_neighbor(cell_prev, current_direction)

        # add cells on a right
        cell_prev = current_cell
        current_direction = (facing_direction+1)%4

        for i in range(math.floor(sensor_R/self.cell_size)):
            cell_prev = self.get_or_create_neighbor(cell_prev, current_direction)

        for element in self.maze:
            print(element)