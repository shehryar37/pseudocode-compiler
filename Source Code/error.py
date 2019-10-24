class Error(object):
    def exception(self, text):
        raise Exception(repr(text))

    def syntax_error(self, current_char, line_number):

        if current_char == 'EOF':
            print('Unexpected {}'.format(
                current_char))
            return

        raise SyntaxError('Unexpected {} at line {}'.format(
            current_char, line_number))

    def token_error(self, current_char, line_number, expected_char):

        if current_char == 'EOF':
            raise EOFError('Unexpected {}'.format(
                current_char))
            return

        raise SyntaxError('Unexpected {} at line {}. Expected {}'.format(
            current_char, line_number, expected_char))

    def type_error(self, text):
        raise TypeError(repr(text))

    def name_error(self, text):
        raise NameError(repr(text))

    def zero_error(self):
        raise ZeroDivisionError('Cannot divide by 0')

    def index_error(self, text):
        raise IndexError(repr(text))

    def unbound_local_error(self, text):
        raise UnboundLocalError(repr(text))

    def reference_error(self, text):
        raise ReferenceError(repr(text))
