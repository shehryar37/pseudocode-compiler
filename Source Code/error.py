class Error(object):
    def syntax_error(self, char, line_number):
        raise SyntaxError('Unexpected ' + str(char) +
                          ' at line ' + str(line_number))
