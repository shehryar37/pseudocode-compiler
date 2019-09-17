class BuiltInFunction():
    def __init__(self, CURRENT_SCOPE):
        self.CURRENT_SCOPE = CURRENT_SCOPE

    def check_function(self, function, parameters, count, types):
        if len(parameters) == count:
            for i in range(0, len(parameters)):
                if not isinstance(parameters[i], types[i]):
                    raise TypeError(function + ': Parameter ' + str(i + 1))
        else:
            raise SyntaxError('Expected ' + str(count) + ' parameter(s).' +
                              ' Got ' + str(len(parameters)) + ' parameter(s)')

        return True

    def check_char(self, parameter):
        if len(parameter) == 1:
            return True
        else:
            return False

    def CHR(self, parameters):
        # CHR(x : INTEGER) RETURNS CHAR
        if self.check_function('CHR', parameters, 1, [int]):
            return chr(parameters[0])

    def ASC(self, parameters):
        # ASC(ThisChar : CHAR) RETURNS INTEGER
        if self.check_function('ASC', parameters, 1, [str]) and self.check_char(parameters[0]):
            return ord(parameters[0])
        else:
            raise TypeError('ASC(CHAR) expects a parameter of type CHAR')

    def LENGTH(self, parameters):
        # LENGTH(ThisString : STRING) RETURNS INTEGER
        if self.check_function('LENGTH', parameters, 1, [str]):
            return len(parameters[0])

    def LEFT(self, parameters):
        # LEFT(ThisString : STRING, x : INTEGER) RETURNS STRING
        if self.check_function('LEFT', parameters, 2, [str, int]):
            return parameters[0][0:parameters[1]]

    def RIGHT(self, parameters):
        # RIGHT(ThisString : STRING, x : INTEGER) RETURNS STRING
        if self.check_function('RIGHT', parameters, 2, [str, int]):
            return parameters[0][-parameters[1]:]

    def MID(self, parameters):
        # MID(ThisString : STRING, x : INTEGER, y : INTEGER) RETURNS STRING
        if self.check_function('MID', parameters, 3, [str, int, int]):
            return parameters[0][parameters[1]:parameters[1] + parameters[2]]

    def CONCAT(self, parameters):
        # CONCAT(String1 : STRING, String2 : STRING [, String3 : STRING]) RETURNS STRING
        if self.check_function('RIGHT', parameters, len(parameters), [str] * len(parameters)) and len(parameters) >= 2:
            concat = ''
            for parameter in parameters:
                concat += parameter
            return concat
        else:
            raise SyntaxError('Expected 2 or more parameters.' +
                              ' Got ' + str(len(parameters)) + ' parameter')

    def INT(self, parameters):
        # INT(x : REAL) RETURNS INTEGER
        if self.check_function('INT', parameters, 1, [float]):
            return int(parameters[0])

    def MOD(self, parameters):
        # MOD(ThisNum : INTEGER, ThisDiv : INTEGER) RETURNS INTEGER
        if self.check_function('MOD', parameters, 2, [int, int]):
            return parameters[0] % parameters[1]

    def DIV(self, parameters):
        # DIV(ThisNum : INTEGER, ThisDiv : INTEGER) RETURNS INTEGER
        if self.check_function('DIV', parameters, 2, [int, int]):
            return parameters[0] // parameters[1]

    def LCASE(self, parameters):
        # LCASE(x : CHAR) RETURNS CHAR
        if self.check_function('LCASE', parameters, 1, [str]) and self.check_char(parameters[0]):
            return parameters[0].lower()

    def UCASE(self, parameters):
        # UCASE (x : CHAR) RETURNS CHAR
        if self.check_function('UCASE', parameters, 1, [str]) and self.check_char(parameters[0]):
            return parameters[0].upper()

    def TONUM(self, parameters):
        # TONUM(ThisDigit : CHAR) RETURNS INTEGER
        if self.check_function('TONUM', parameters, 1, [str] and self.check_char(parameters[0])):
            if parameters[0].isnum():
                return int(parameters[0])
            else:
                raise ValueError('Cannot parse' +
                                 str(parameters[0]) + ' to INTEGER')

    def TOSTRING(self, parameters):
        # TOSTRING(ThisNumber : INTEGER or REAL) RETURNS STRING
        if self.check_function('TOSTRING', parameters, 1, [(int, float)]):
            return str(parameters[0])

    def ONECHAR(self, parameters):
        # ONECHAR(ThisString : STRING, Position: INTEGER) RETURNS CHAR
        if self.check_function('ONECHAR', parameters, 2, [str, int]):
            return parameters[0][parameters[1] - 1]

    def EOF(self, parameters):
        if self.check_function('EOF', parameters, 1, [str]):
            file = self.CURRENT_SCOPE.VALUES.get(parameters[0])
            if file != None:
                back = file.tell()
                line = file.readline()
                file.seek(back)
                if len(line) > 0:
                    return False
                else:
                    return True
            else:
                FileNotFoundError(parameters[0])

    # ----------------------------------------
    # LEGACY FUNCTIONS
    # ----------------------------------------

    def SUBSTR(self, parameters):
        self.MID(parameters)

    def CHARACTERCOUNT(self, parameters):
        self.LENGTH(parameters)
