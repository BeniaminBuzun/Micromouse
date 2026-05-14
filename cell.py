class Cell:

    def __init__(self, posX, posY):
        # Connections to other cells
        self.pos = (posX, posY)
        self.north = None
        self.south = None
        self.west = None
        self.east = None

    def __str__(self):
        # Check connections
        n = "N" if self.north else " "
        s = "S" if self.south else " "
        w = "W" if self.west else " "
        e = "E" if self.east else " "
        print(self.pos)
        # Return a formatted visual string
        return (
            f"Cell {self.pos}\n"
            f"  {n}  \n"
            f"{w}[+]{e}\n"
            f"  {s}  \n"
        )