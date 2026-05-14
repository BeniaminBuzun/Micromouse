class Cell:
    def __init__(self, posX, posY):
#         connections to other cells
        self.pos = (posX, posY)
        self.north = None
        self.south = None
        self.west = None
        self.east = None
        
    def __str__(self):
        return self.pos
