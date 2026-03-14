# compilator.py
from block_print import PrintBlock
from block_int import IntBlock

class Compilator:
    def __init__(self, code):
        self.code = code
        self.cods = self.code.split()
        self.bt = []

    def run(self):
        i = 0
        self.bt.append("START")
        while i < len(self.cods):
            token = self.cods[i]

            if token == "print":
                blk = PrintBlock(token, self.cods[i+1])
                blk.execute(self.bt)
                i += 1  # skip argument
            elif token == "int":
                blk = IntBlock(token, self.cods[i+1], self.cods[i+3])
                blk.execute(self.bt)
                i += 3  # skip name, =, value

            i += 1

        self.bt.append("HALT")
        return self.bt
