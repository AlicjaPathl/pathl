# block_print.py

class PrintBlock:
    def __init__(self, token, next_token):
        self.token = token        # np. "print"
        self.next_token = next_token  # np. '"hellow"'

    def execute(self, bt):
        bt.append("PUSH")
        bt.append(self.next_token)
        bt.append("PRINT")
