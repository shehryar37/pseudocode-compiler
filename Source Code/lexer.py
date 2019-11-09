from error import Error

class Token():
    def __init__(self, type, value):
        self.type = type
        self.value = value

class Lexer():
    def __init__(self, code):
        """Initializes an instance of Lexer

        Arguments:
            code {str} -- The raw text written by the user
        """
        self.code = code
        self.line_number = 1
        self.position = 0
        self.current_char = code[self.position]

        # Contains all words(tokens) recognized by this language
        self.tokens = {
            'KEYWORD': ['INPUT', 'OUTPUT', 'DECLARE', 'OF', 'IF', 'THEN', 'ELSEIF',
                        'ELSE', 'ENDIF', 'FOR', 'TO', 'STEP', 'ENDFOR', 'REPEAT',
                        'UNTIL', 'WHILE', 'ENDWHILE', 'CASE', 'OF', 'OTHERWISE', 'ENDCASE', 'PROCEDURE', 'ENDPROCEDURE', 'FUNCTION', 'ENDFUNCTION', 'RETURN', 'CALL', 'BYVAL', 'BYREF', 'OPENFILE', 'READFILE', 'WRITEFILE', 'CLOSEFILE', 'TYPE', 'ENDTYPE', 'CONSTANT'
                        ],
            'BUILTIN_FUNCTION': ['CHR', 'ASC', 'LENGTH', 'LEFT', 'RIGHT', 'MID',
                                 'CONCAT', 'INT', 'LCASE', 'UCASE', 'TONUM', 'TOSTRING', 'SUBSTR', 'ONECHAR', 'CHARACTERCOUNT', 'EOF'
                                 ],
            'OPERATION': ['+', '-', '/', '*', 'DIV', 'MOD', '^'
                          ],
            'PARENTHESIS': ['(', ')', '{', '}', '[', ']'
                            ],
            'COMPARISON': ['>', '<', '='
                           ],
            'BOOLEAN': ['TRUE', 'FALSE'
                        ],
            'LOGICAL': ['AND', 'OR', 'NOT'
                        ],
            'FILE_MODE': ['READ', 'WRITE', 'APPEND'
                          ]
        }

    def next_token(self):
        """Returns the next token in the text

        Returns:
            Token -- The token made from the current characters in the raw text
        """
        while self.current_char != 'EOF':
            if self.current_char.isspace():
                self.advance()
            elif self.current_char.isalpha():
                return self.make_word()
            elif self.current_char.isnumeric():
                return self.make_number()
            elif self.current_char == '"':
                self.advance()
                token = Token('STRING', self.make_string())
                self.advance()
                return token
            elif self.current_char in self.tokens['OPERATION']:
                token = Token('OPERATION', self.current_char)
                self.advance()
                return token
            elif self.current_char in self.tokens['PARENTHESIS']:
                token = Token('PARENTHESIS', self.current_char)
                self.advance()
                return token
            elif self.current_char == '<' and self.peek() == '-':
                self.advance()
                self.advance()
                return Token('ASSIGNMENT', '<-')
            elif self.current_char == '.' and self.peek() == '.':
                self.advance()
                self.advance()
                return Token('RANGE', '..')
            elif self.current_char == '#':
                token = self.ignore_line()
                return token
            elif self.current_char == '.':
                self.advance()
                return Token('PERIOD', '.')
            elif self.current_char == ':':
                token = Token('COLON', self.current_char)
                self.advance()
                return token
            elif self.current_char == ',':
                token = Token('COMMA', self.current_char)
                self.advance()
                return token
            elif self.current_char in self.tokens['COMPARISON']:
                token = Token('COMPARISON', self.make_comparison())
                self.advance()
                return token
            else:
                Error.syntax_error(Error, self.current_char, self.line_number)

        return Token('EOF', 'EOF')

    def advance(self):
        """Advances the Lexer instance by one character
        """
        self.position += 1

        if self.position > len(self.code) - 1:
            # The end of the file has been reached
            self.current_char = 'EOF'
        else:
            self.current_char = self.code[self.position]

    def peek(self):
        """Peeks at the next character in the code without actually advancing

        Returns:
            str -- The next character in the code
        """
        peek_position = self.position + 1
        if peek_position > len(self.code) - 1:
            # The end of the file has been reached
            self.current_char = 'EOF'
        else:
            return self.code[peek_position]

    def make_string(self):
        """Makes a string out of the characters following the " before the next "

        Returns:
            str -- The string contained inside " and "
        """
        string = ''
        while self.current_char != '"' and self.current_char != 'EOF':
            string += self.current_char
            self.advance()

        return string

    def make_word(self):
        """Checks the current word against the Lexer word dictionary

        Returns:
            Token -- the word formed and its type
        """
        word = ''
        while self.current_char.isalnum() and self.current_char != 'EOF':
            word += self.current_char
            self.advance()

        if word in self.tokens['KEYWORD']:
            return Token('KEYWORD', word)
        elif word in self.tokens['BUILTIN_FUNCTION']:
            return Token('BUILTIN_FUNCTION', word)
        elif word in self.tokens['OPERATION']:
            return Token('OPERATION', word)
        elif word in self.tokens['LOGICAL']:
            return Token('LOGICAL', word)
        elif word in self.tokens['BOOLEAN']:
            return Token('BOOLEAN', word)
        elif word in self.tokens['FILE_MODE']:
            return Token('FILE_MODE', word)
        elif word == 'EOL':
            self.line_number += 1
            return self.next_token()
        else:
            return Token('VARIABLE', word)

    def make_number(self):
        """Forms a number

        Returns:
            Token -- the number formed and its type
        """
        number = ''
        while self.current_char.isnumeric() or (self.current_char == '.' and self.peek() != '.'):
            number += self.current_char
            self.advance()

        if number.find('.') == -1:
            return Token('INTEGER', int(number))
        else:
            return Token('REAL', float(number))

    def make_comparison(self):
        """Forms a comparison operator

        Returns:
            Token -- the operator formed and its type
        """
        char = self.current_char

        if char == '=':
            if self.peek() == '<' or self.peek() == '>':
                self.advance()
                char += self.current_char
        elif char == '<':
            if self.peek() == '>' or self.peek() == '=':
                self.advance()
                char += self.current_char
        elif char == '>':
            if self.peek() == '=':
                self.advance()
                char += self.current_char

        return char

    def ignore_line(self):
        """Ignores all tokens until an EOL is seen

        Returns:
            Token -- The next non-commented Token formed by the code
        """
        line = self.line_number

        # Line changes after a new line

        while self.line_number == line:
            self.advance()
            token = self.next_token()

        return token
