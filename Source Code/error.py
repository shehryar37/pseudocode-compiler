class Error():
    """Passes all errors coming from lexer.py, interpreter.py or syntax_analysis.py to the console window

    Raises:
        Exception: Generic Exception
        SyntaxError: When the SyntaxAnalysis class gets an unexpected Token
        EOFError: When a block does not end
        TypeError: When the value does not match the data_type attribute of the instance
        NameError: When the instance being used has not been declared
        ZeroDivisionError: When dividing by 0
        IndexError: When Array is out of bounds
        UnboundLocalError: When an instance has been declared but its value is None
        ReferenceError: An instance to be passed into BYREF parameter is not an instance
    """

    def exception(self, text):
        """Raises a generic Error

        Arguments:
            text {str} -- The text to display on the console window
        """
        raise Exception(repr(text))

    def syntax_error(self, current_char, line_number):
        """Raises a syntax error and shows the token and line number on the console window

        Arguments:
            text {str} -- The text to display on the console window
        """

        # Checks if the end of the file has been reached
        if current_char == 'EOF':
            print('Unexpected {}'.format(
                current_char))
            return
        else:
            raise SyntaxError('Unexpected {} at line {}'.format(
                current_char, line_number))

    def token_error(self, current_char, line_number, expected_char):
        """Raises a syntax error and shows the token, line number and expected token on the console window

        Arguments:
            text {str} -- The text to display on the console window
        """

        # Checks if the end of the file has been reached
        if current_char == 'EOF':
            raise EOFError('Unexpected {}'.format(
                current_char))
            return
        else:
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

    def eof_error(self, text):
        raise EOFError(repr(text))
