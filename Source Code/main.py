from analyzer import Analyzer
from error import Error
from interpreter import Interpreter
import sys

# Comment to view call stacks
# sys.tracebacklimit = 0


def main():
    file = open('console.psc', 'r')

    line = file.readline()
    code = line
    while len(line) > 0:

        line = file.readline()
        code += ' EOL ' + line

    analyzer = Analyzer(code)
    interpreter = Interpreter(analyzer)


main()
