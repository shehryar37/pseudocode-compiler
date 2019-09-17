from lexer import Lexer
from error import Error
from ast import *
from tokens import Token

class SyntaxAnalysis():
    def __init__(self, code):
        self.code = code
        self.lexer = Lexer(code)
        self.current_token = self.lexer.next_token()

    def block(self, end_block):
        statement_list = []
        while self.current_token.value not in end_block:
            statement_list.append(self.statement())

        block = Block(statement_list)
        return block

    def statement(self):
        token = self.current_token
        if token.type == 'KEYWORD':
            if token.value == 'PROCEDURE':
                node = self.procedure()
            elif token.value == 'FUNCTION':
                node = self.function()
            elif token.value == 'CALL':
                node = self.call()
            elif token.value == 'RETURN':
                node = self.return_value()
            if token.value == 'INPUT':
                node = self.assign_input()
            elif token.value == 'OUTPUT':
                node = self.output()
            elif token.value == 'DECLARE':
                node = self.declarations()
            elif token.value == 'IF':
                node = self.selection()
            elif token.value == 'CASE':
                node = self.case()
            elif token.value == 'FOR':
                node = self.iteration()
            elif token.value == 'REPEAT':
                node = self.post_condition_loop()
            elif token.value == 'WHILE':
                node = self.pre_condition_loop()
            elif token.value == 'OPENFILE':
                node = self.open_file()
            elif token.value == 'READFILE':
                node = self.read_file()
            elif token.value == 'WRITEFILE':
                node = self.write_file()
            elif token.value == 'CLOSEFILE':
                node = self.close_file()
            elif token.value == 'TYPE':
                node = self.declare_type()
        elif token.type == 'VARIABLE':
            node = self.assignment()
        else:
            Error().syntax_error(self.current_token.value, self.lexer.line_number)

        return Statement(node)

    def check_token(self, token_type):
        if self.current_token.type == token_type:
            token = self.current_token
            self.current_token = self.lexer.next_token()
        else:
            Error().syntax_error(self.current_token.value, self.lexer.line_number)

    def check_token_value(self, token_value):
        if self.current_token.value == token_value:
            token = self.current_token
            self.current_token = self.lexer.next_token()
        else:
            Error().syntax_error(self.current_token.value, self.lexer.line_number)

    # START: Operation Handling

    def output(self):
        self.check_token('KEYWORD')
        return Output(self.expression())

    def expression(self):
        node = self.term()
        while self.current_token.value in ('+', '-'):
            if self.current_token.value == '+':
                token = self.current_token
                self.check_token('OPERATION')
            elif self.current_token.value == '-':
                token = self.current_token
                self.check_token('OPERATION')

            node = BinaryOperation(node, token, self.term())

        return node

    def term(self):
        node = self.factor()

        while self.current_token.value in ('*', '/'):
            token = self.current_token
            self.check_token('OPERATION')

            node = BinaryOperation(node, token, self.factor())

        return node

    def factor(self):
        token = self.current_token
        if token.type == 'OPERATION':
            if token.value == '+':
                self.check_token('OPERATION')
                node = UnaryOperation(token, self.factor())
            elif token.value == '-':
                self.check_token('OPERATION')
                node = UnaryOperation(token, self.factor())
        elif token.type == 'INTEGER':
            self.check_token('INTEGER')
            node = Value(token)
        elif token.type == 'REAL':
            self.check_token('REAL')
            node = Value(token)
        elif token.type == 'BOOLEAN':
            if token.value == 'TRUE':
                token.value = True
            elif token.value == 'FALSE':
                token.value = False
            self.check_token('BOOLEAN')
            node = Value(token)
        elif token.type == 'STRING':
            self.check_token('STRING')
            node =  Value(token)
        elif token.type == 'BUILTIN_FUNCTION':
            node = self.builtin_function()
        elif token.value == 'CALL':
            node = self.call()
        elif token.type == 'PARENTHESIS':
            self.check_token_value('(')
            node = self.expression()
            self.check_token_value(')')
        elif token.type == 'VARIABLE':
            node = self.variable_value()

        return node

    # END: Operation Handling

    # START: Variable Declaration

    def declarations(self):
        # DECLARE variable_declarations COLON type
        self.check_token('KEYWORD')
        declarations = Declarations(self.variable_declarations())
        return declarations

    def variable_declarations(self):
        # variable_declaration COMMA (variable_declaration)*

        variables = [VariableName(self.current_token)]
        self.check_token('VARIABLE')

        while self.current_token.type == 'COMMA':
            self.check_token('COMMA')
            variables.append(VariableName(self.current_token))
            self.check_token('VARIABLE')

        self.check_token('COLON')

        data_type = self.data_type()

        declarations = [
            VariableDeclaration(variable, data_type)
            for variable in variables
        ]

        return declarations

    def data_type(self):
        token = self.current_token
        self.check_token('VARIABLE')

        if token.value != 'ARRAY':
            data_type = DataType(token)
            return data_type
        else:
            # ARRAY PARENTHESIS dimensions PARENTHESIS OF type
            self.check_token_value('[')
            dimensions = self.dimensions()
            self.check_token_value(']')
            self.check_token_value('OF')
            data_type = self.data_type()

            array = Array(dimensions, data_type)
            return array

    def dimensions(self):
        # expression COLON expression (COMMA expression COLON expression)*
        dimensions = []
        lower_bound = self.bound()
        self.check_token('COLON')
        upper_bound = self.bound()
        dimensions.append(Dimension(lower_bound, upper_bound))

        while self.current_token.type == 'COMMA':
            self.check_token('COMMA')
            lower_bound = self.bound()
            self.check_token('COLON')
            upper_bound = self.bound()
            dimensions.append(Dimension(lower_bound, upper_bound))

        return Dimensions(dimensions)

    def bound(self):
        return Bound(self.expression())

    # END: Variable Declaration

    # START: Variable Assignment

    def assignment(self):
        left = self.variable_name()
        # Make updates for arrays here
        self.check_token('ASSIGNMENT')
        right = self.expression()
        assignment = Assignment(left, right)

        return assignment

    def variable_name(self):
        # variable (indexes)*
        object = VariableName(self.current_token)
        self.check_token('VARIABLE')

        indexes = []

        if self.current_token.type == 'PARENTHESIS':
           self.check_token_value('[')
           indexes.append(self.index())
           while self.current_token.type == 'COMMA':
               self.check_token('COMMA')
               indexes.append(self.index())
           self.check_token_value(']')

           element = Element(object, indexes)
           return element

        return object

    def index(self):
        return Index(self.expression())

    def variable_value(self):
        object = VariableValue(self.current_token)
        self.check_token('VARIABLE')

        indexes = []

        if self.current_token.type == 'PARENTHESIS':
           self.check_token_value('[')
           indexes.append(self.index())
           while self.current_token.type == 'COMMA':
               self.check_token('COMMA')
               indexes.append(self.index())
           self.check_token_value(']')

            # TODO September 17, 2019: Add ElementValue AST class
            # TODO September 17, 2019: Allow usage of assigned arrays

           element = ElementValue(object, indexes)
           return element

        return object

    # END: Variable Assignment

    # START: Input

    def assign_input(self):
        self.check_token('KEYWORD')

        assign_input = AssignInput(self.input())
        return assign_input

    def input(self):
        if self.current_token.type == 'STRING':
            input_string = self.current_token.value
            self.check_token('STRING')
            var_node = VariableName(self.current_token)
            self.check_token('VARIABLE')
        else:
            input_string = '> '
            var_node = VariableName(self.current_token)
            self.check_token('VARIABLE')

        node = Input(input_string, var_node)
        return node

    # END: Input

    def logical_expression(self):
        node = self.logical_term()
        while self.current_token.value == 'AND':
            token = self.current_token
            self.check_token('LOGICAL')

            node = BinaryLogicalOperation(node, token, self.logical_term())

        return node

    def logical_term(self):
        node = self.logical_factor()

        while self.current_token.value == 'OR':
            token = self.current_token
            self.check_token('LOGICAL')

            node = BinaryLogicalOperation(node, token, self.logical_factor())

        return node

    def logical_factor(self):
        token = self.current_token
        if token.value == 'NOT':
            self.check_token('LOGICAL')
            node = UnaryLogicalOperation(token, self.logical_factor())
        elif token.type == 'PARENTHESIS':
            self.check_token_value('(')
            node = self.logical_expression()
            self.check_token_value(')')
        elif token.value == 'CALL':
            node = self.call()
        elif token.type == 'BOOLEAN':
            node = self.factor()
        elif token.type == 'BUILTIN_FUNCTION':
            node = self.builtin_function()
        else:
            node = self.condition()

        return node

    def condition(self):
        # expression COMPARISON expression
        left = self.expression()
        comparison = self.current_token
        self.check_token('COMPARISON')
        right = self.expression()

        condition = Condition(left, comparison, right)
        return condition

    def case_condition(self, left):
        # variable (TO, .., ,) expression

        options = []
        options.append(self.expression())

        if self.current_token.value == 'TO' or self.current_token.value == '..':
            if self.current_token.value == 'TO':
                self.check_token_value('TO')
            else:
                self.check_token_value('..')
            start = options[-1]
            del options[-1]
            right = Range(start, self.expression())
        else:
            while self.current_token.type != 'COLON':
                if self.current_token.type == 'COMMA':
                    self.check_token('COMMA')
                    options.append(Value(self.expression()))

            right = Options(options)


        self.check_token('COLON')

        comparison = Token('COMPARISON', '=')

        condition = Condition(left, comparison, right)
        return condition

    # START: Selection

    def selection(self):
        selection_list = []

        while self.current_token.value != 'ENDIF':
            selection_list.append(self.selection_statement())

        self.check_token_value('ENDIF')

        selection = Selection(selection_list)
        return selection

    def selection_statement(self):
        # (IF|ELSEIF condition THEN
        #   block) | ELSE block
        if self.current_token.value != 'ELSE': #FIX THIS
            self.check_token('KEYWORD')
            condition = self.logical_expression()
            self.check_token_value('THEN')
            block = self.block(['ELSE', 'ELSEIF', 'ENDIF'])
        else:
            self.check_token('KEYWORD')
            condition = None
            block = self.block(['ENDIF'])

        selection_statement = SelectionStatement(condition, block)
        return selection_statement

    # END: Selection

    # START: Case

    def case(self):
        # CASE OF variable
        # CASE expression COLON block

        case_list = []

        self.check_token('KEYWORD')
        self.check_token_value('OF')
        left = self.variable_name()

        while self.current_token.value != 'ENDCASE':
            case_list.append(self.case_statement(left))

        self.check_token_value('ENDCASE')

        return Case(case_list)


    def case_statement(self, left):
        if self.current_token.value != 'OTHERWISE':
            self.check_token_value('CASE')
            condition = self.case_condition(left)

            block = self.block(['CASE', 'OTHERWISE', 'ENDCASE'])
        else:
            condition = None
            self.check_token('KEYWORD')
            block = self.block(['ENDCASE'])

        return SelectionStatement(condition, block)

    # END: Case

    # START: Iteration

    def iteration(self):
        # FOR VARIABLE ASSIGNMENT INTEGER TO INTEGER (STEP INTEGER)
        #   block
        # ENDFOR
        self.check_token('KEYWORD')
        variable = self.variable_name()
        self.check_token('ASSIGNMENT')
        start = self.expression()
        assignment = Assignment(variable, start)
        self.check_token_value('TO')
        end = self.expression()

        if self.current_token.value == 'STEP':
            self.check_token('KEYWORD')
            step = self.expression()
        else:
            step = Value(Token('INTEGER', 1))

        block = self.block(['ENDFOR'])
        self.check_token('KEYWORD')

        iteration = Iteration(variable, assignment, end, step, block)
        return iteration

    # END: Iteration

    # START: Post-condition Loop

    def post_condition_loop(self):
        # REPEAT
        #   block
        # UNTIL condition
        self.check_token('KEYWORD')
        block = self.block(['UNTIL'])
        self.check_token('KEYWORD')
        condition = self.logical_expression()
        loop = Loop(condition, block, False)

        return loop

    # END: Post-Condition Loop

    # START: Pre-condition Loop

    def pre_condition_loop(self):
        # WHILE condition
        #   block
        # ENDWHILE
        self.check_token('KEYWORD')
        condition = self.logical_expression()
        block = self.block(['ENDWHILE'])
        self.check_token('KEYWORD')
        loop = Loop(condition, block, True)

        return loop

    # END: Pre-Condition Loop

    # START: Built-in Function

    def builtin_function(self):
        name = self.current_token
        self.check_token('BUILTIN_FUNCTION')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.expression())
            if self.current_token.type == 'COMMA':
                self.check_token('COMMA')
            else:
                break

        self.check_token_value(')')

        return BuiltInFunction(name, parameters)

    # END: Built-in Function

    def parameter(self):
        # VARIABLE COLON DATA_TYPE
        scope_type = self.current_token
        if self.current_token.value in ['BYREF', 'BYVAL']:
            self.check_token('KEYWORD')
        variable = VariableName(self.current_token)
        self.check_token('VARIABLE')
        self.check_token('COLON')
        data_type = self.data_type()

        node = Parameter(variable, data_type, scope_type)
        return node

    def call(self):
        self.check_token('KEYWORD')
        name = Value(self.current_token)
        self.check_token('VARIABLE')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.expression())
            if self.current_token.type == 'COMMA':
                self.check_token('COMMA')
            else:
                break

        self.check_token_value(')')

        return Call(name, parameters)


    # START: Procedure

    def procedure(self):
        self.check_token('KEYWORD')
        name = Value(self.current_token)
        self.check_token('VARIABLE')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.parameter())
            if self.current_token.type == 'COMMA':
                self.check_token('COMMA')
            else:
                break

        self.check_token_value(')')
        node = Function(name, parameters, self.block(['ENDPROCEDURE']), None)
        self.check_token('KEYWORD')

        return node

    # END: Procedure

    # START: Function

    def function(self):
        self.check_token('KEYWORD')
        name = Value(self.current_token)
        self.check_token('VARIABLE')
        self.check_token_value('(')

        parameters = []

        while self.current_token.value != ')':
            parameters.append(self.parameter())
            if self.current_token.type == 'COMMA':
                self.check_token('COMMA')
            else:
                break

        self.check_token_value(')')
        self.check_token('COLON')

        return_type = self.data_type()

        node = Function(name, parameters, self.block(['ENDFUNCTION']), return_type)
        self.check_token('KEYWORD')

        return node

    def return_value(self):
        self.check_token('KEYWORD')
        return self.expression()

    # END: Function

    # START: File

    def open_file(self):
        self.check_token('KEYWORD')
        file_name = Value(self.current_token)
        self.check_token('STRING')
        self.check_token_value('FOR')
        file_mode = FileMode(self.current_token)
        self.check_token('FILE_MODE')

        return File(file_name, file_mode)

    def read_file(self):
        self.check_token('KEYWORD')
        file_name = VariableValue(self.current_token)
        self.check_token('STRING')
        self.check_token('COMMA')
        variable = VariableName(self.current_token)
        self.check_token('VARIABLE')

        return ReadFile(file_name, variable)

    def write_file(self):
        self.check_token('KEYWORD')
        file_name = VariableValue(self.current_token)
        self.check_token('STRING')
        self.check_token('COMMA')
        line = self.expression()

        return WriteFile(file_name, line)

    def close_file(self):
        self.check_token('KEYWORD')
        file_name = VariableName(self.current_token)
        self.check_token('STRING')

        return CloseFile(file_name)

    # END: File

    # START: Type

    def declare_type(self):
        self.check_token('KEYWORD')
        type_name = Value(self.current_token)
        self.check_token('VARIABLE')
        block = self.block(['ENDTYPE'])
        self.check_token('KEYWORD')

        return TypeDeclaration(type_name, block)

    # END: Type
