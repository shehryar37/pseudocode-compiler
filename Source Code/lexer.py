from tokens import Token
from error import Error


class Lexer():
    def __init__(self, code):
        self.code = code
        self.line_number = 1
        self.position = 0
        self.current_char = code[self.position]

        self.tokens = {
            'KEYWORD': ['INPUT', 'OUTPUT', 'DECLARE', 'OF', 'IF', 'THEN', 'ELSEIF', 'ELSE', 'ENDIF', 'FOR', 'TO', 'STEP', 'ENDFOR', 'REPEAT', 'UNTIL', 'WHILE', 'ENDWHILE', 'CASE', 'OF', 'OTHERWISE', 'ENDCASE', 'PROCEDURE', 'ENDPROCEDURE', 'FUNCTION', 'ENDFUNCTION', 'RETURN', 'CALL', 'BYVAL', 'BYREF', 'OPENFILE', 'READFILE', 'WRITEFILE', 'CLOSEFILE', 'TYPE', 'ENDTYPE'],
            'BUILTIN_FUNCTION': ['CHR', 'ASC', 'LENGTH', 'LEFT', 'RIGHT', 'MID', 'CONCAT', 'INT', 'MOD', 'DIV', 'LCASE', 'UCASE', 'TONUM', 'TOSTRING', 'SUBSTR', 'ONECHAR', 'CHARACTERCOUNT', 'EOF'],
            'OPERATION': ['+', '-', '/', '*'],
            'PARENTHESIS': ['(', ')', '{', '}', '[', ']'],
            'COMPARISON': ['>', '<', '='],
            'BOOLEAN': ['TRUE', 'FALSE'],
            'LOGICAL': ['AND', 'OR', 'NOT'],
            'FILE_MODE': ['READ', 'WRITE', 'APPEND']
            # TODO July 24, 2019: Add functionality for comment blocks
        }

    def next_token(self):
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
        self.position += 1
        if self.position > len(self.code) - 1:
            self.current_char = 'EOF'
        else:
            self.current_char = self.code[self.position]

    def peek(self):
        peek_position = self.position + 1
        if peek_position > len(self.code) - 1:
            self.current_char = 'EOF'
        else:
            return self.code[peek_position]

    def make_string(self):
        string = ''
        while self.current_char != '"':
            string += self.current_char
            self.advance()

        return string

    def make_word(self):
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
        number = ''
        while self.current_char.isnumeric() or (self.current_char == '.' and self.peek() != '.'):
            number += self.current_char
            self.advance()

        if number.find('.') == -1:
            return Token('INTEGER', int(number))
        else:
            return Token('REAL', float(number))

    def make_comparison(self):
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
