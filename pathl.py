import compilator
comp = compilator.Compilator()
code = """print "hellow"
int x = 10"""
interpreter = comp(code)
result = interpreter.run()
print(result)
