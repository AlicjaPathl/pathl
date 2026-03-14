class MiniInterpreter:
    def __init__(self, code):
        self.code = code
        self.cods = self.code.split()
        self.bt = []
        # Mapa: nazwa instrukcji → kod binarny
        self.comp = {
            "START": "1",
            "PRINT": "1010",
            "PUSH": "1001",
            "HALT": "0",
            "int": "1100"
        }

    def run(self):
        i = 0
        self.bt.append("START")
        while i < len(self.cods):
            actual = self.cods[i]
            if actual == "print":
                self._p(i, println=False)
            elif actual == "println":
                self._p(i, println=True)
            elif actual == "int":
                self._var(i)
            i += 1
        self.bt.append("HALT")
        return self.bt

    def _p(self, index, println=False):
        self.bt.append("PUSH")
        self.bt.append(self.cods[index + 1])
        self.bt.append("PRINT")
        if println:
            self.bt.append(r"\n")

    def _var(self, index):
        if index + 3 < len(self.cods):
            self.bt.append("PUSH")
            self.bt.append(self.cods[index + 1])
            self.bt.append(self.cods[index + 3])

    def show_codes(self):
        byte_list = []
        bin_list = []

        for token in self.bt:
            if token in self.comp:
                byte_list.append(token)          # nazwa instrukcji
                bin_list.append(self.comp[token])  # binarny kod
            else:
                byte_list.append(token)
                bin_list.append(token)

        print("Byte code:", byte_list)
        print("Binary code:", bin_list)


# Przykład użycia
code = """print "hellow" 
int x = 10"""
interpreter = MiniInterpreter(code)
interpreter.run()
interpreter.show_codes()
