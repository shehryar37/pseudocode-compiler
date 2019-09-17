from syntax_analysis import SyntaxAnalysis
from interpreter import Interpreter


def main():
    file = open('console.psc', 'r')
    line = file.readline()

    code = line

    while len(line) > 0:
        line = file.readline()
        code += ' EOL ' + line

    parser = SyntaxAnalysis(code)
    interpreter = Interpreter(parser)
    interpreter.interpret()


main()
