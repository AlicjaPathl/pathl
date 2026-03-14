# block_int.py

class IntBlock:
    def __init__(self, token, name, value):
        self.token = token  # np. "int"
        self.name = name
        self.value = value

    def execute(self, bt):
        bt.append("PUSH")
        bt.append(self.name)
        bt.append(self.value)
