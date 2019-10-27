from function import BuiltInFunction
from scope import Scope
from error import Error
from symbol_table import *

class Interpreter():
    def __init__(self, parser):
        self.parser = parser
        self.SCOPES = {}
        self.PARENT_SCOPE = None
        self.SCOPES['GLOBAL'] = Scope(self.PARENT_SCOPE, [], None, None)
        self.CURRENT_SCOPE = self.SCOPES.get('GLOBAL')

    def interpret(self):
        tree = self.parser.block(['EOF'])
        # self.parser.check_token_value('EOF')
        self.visit(tree)

    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        Error().exception('No visit_{} method'.format(type(node).__name__))

    def visit_function(self, node):
        method_name = node.name.value
        visitor = getattr(BuiltInFunction(self.CURRENT_SCOPE),
                          method_name, self.generic_visit)
        return visitor(node.parsed_parameters)

    def visit_EmptyLine(self, token):
        return None

    def visit_Block(self, node):
        for statement in node.block:
            node = self.visit(statement)

            if node != None:
                return node

    def visit_Statement(self, node):
        return self.visit(node.statement)

    # START: Operation Handling

    def visit_BinaryOperation(self, node):

        if node.operation.value == '+':
            return self.visit(node.left) + self.visit(node.right)
        elif node.operation.value == '-':
            return self.visit(node.left) - self.visit(node.right)
        elif node.operation.value == '*':
            return self.visit(node.left) * self.visit(node.right)
        elif node.operation.value == '/':

            right = self.visit(node.right)

            if right == 0:
                Error().zero_error()

            return self.visit(node.left) / right
        elif node.operation.value == 'DIV':

            right = self.visit(node.right)

            if right == 0:
                Error().zero_error()

            return self.visit(node.left) // right
        elif node.operation.value == 'MOD':

            right = self.visit(node.right)

            if right == 0:
                Error().zero_error()

            return self.visit(node.left) % right

        elif node.operation.value == '^':
            return self.visit(node.left) ** self.visit(node.right)

    def visit_UnaryOperation(self, node):
        if node.op.value == '+':
            return +self.visit(node.expr)
        elif node.op.value == '-':
            return -self.visit(node.expr)

    def visit_Value(self, node):
        return node.token.value

    # END: Operation Handling

    # START: Variable Declaration

    def visit_Declarations(self, declarations):
        for declaration in declarations.declarations:
            self.visit(declaration)

    def visit_VariableDeclaration(self, declaration):
        var_name = self.visit(declaration.variable)

        variable_metadata = Variable(self.visit(declaration.data_type))

        self.CURRENT_SCOPE.SYMBOL_TABLE.add(var_name, variable_metadata)

    def visit_DataType(self, data_type):
        if data_type.value in self.CURRENT_SCOPE.DATA_TYPES.keys():
            return data_type.value
        else:
            Error().type_error('TYPE {} has not been initialized'.format(data_type.value))

    # END: Variable Declaration

    # START: Array Declaration

    def visit_Array(self, node):
        data_type = self.visit(node.data_type)
        dimensions = self.visit(node.dimensions)

        array = Array(dimensions, data_type)

        return array

    def visit_Dimensions(self, dimensions):
        dimension_list = []
        for dimension in dimensions.dimensions:
            dimension_list.append(self.visit(dimension))

        return dimension_list

    def visit_Dimension(self, dimension):

        lower_bound = self.visit(dimension.lower_bound)
        upper_bound = self.visit(dimension.upper_bound)

        if not upper_bound > lower_bound:
            Error().index_error('Upper bound cannot be lesser than or equal to lower bound')

        return [lower_bound, upper_bound]

    def visit_Bound(self, bound):
        return self.visit(bound.value)

    # END: Array Declaration

    # START: Type Declaration

    def visit_TypeDeclaration(self, node):
        type_name = self.visit(node.type_name)

        # Creates a new scope with the TYPE name
        self.SCOPES[type_name] = scope = Scope(self.CURRENT_SCOPE, [], [], node.block)

        # Scopes into TYPE
        scope.PARENT_SCOPE = self.CURRENT_SCOPE
        self.CURRENT_SCOPE = scope
        self.PARENT_SCOPE = scope.PARENT_SCOPE

        self.visit(scope.block)

        # Gets all the declarations within TYPE
        children = {'SYMBOL_TABLE' : self.CURRENT_SCOPE.SYMBOL_TABLE}

        # Scopes out of TYPE
        self.CURRENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE
        self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE

        self.CURRENT_SCOPE.DATA_TYPES[type_name] = type(type_name, (), children)

    def visit_TypeAssignment(self, node):
        self.visit(node.object)
        # TODO September 25, 2019: Complete this piece of code

    # END: Type Declaration

    # START: Variable Assignment

    def visit_Assignment(self, node):
        var_name = self.visit(node.variable)
        value = self.visit(node.expression)

        if type(var_name) is not list:
            data_type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name)
            if data_type is None:
                Error.name_error(var_name)

            if type(value) is not list:
                self.check_type(data_type, value, var_name)
                self.CURRENT_SCOPE.add(var_name, value)
            else:
                # FIXME September 20, 2019: Does not work for 2D+ ARRAY
                for i in range(len(data_type.dimensions)):
                    if len(value) == (data_type.dimensions[i][1] - data_type.dimensions[i][0] + 1):
                        for j in range(data_type.dimensions[i][0], data_type.dimensions[i][1] + 1):

                            offset = j - data_type.dimensions[i][0]

                            self.check_type(
                                 data_type.data_type, value[offset], var_name)

                            if self.CURRENT_SCOPE.VALUES.get(var_name):
                                self.CURRENT_SCOPE.VALUES[variable]['[{}]'.format(str(j))] = value[offset]
                            else:
                                self.CURRENT_SCOPE.add(
                                    var_name, {'[{}]'.format(str(j)): value[offset]})
                    else:
                        Error().index_error(var_name)
        else:
            data_type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name[0])
            if data_type is not None:
                self.check_type(data_type.data_type, value, var_name[0])

                dimensions = var_name[1]

                # Checks if the number of dimensions(rank) of both arrays is the same
                if len(dimensions) != len(data_type.dimensions):
                    Error().index_error(var_name[0])

                # Checks if the index is within upper and lower bound limits
                for i in range(len(dimensions)):
                    if dimensions[i] < data_type.dimensions[i][0] or dimensions[i] > data_type.dimensions[i][1]:
                        Error().index_error(var_name[0])

                    # TODO September 20, 2019: Try making this elegant (remove if)
                    if self.CURRENT_SCOPE.VALUES.get(var_name[0]):
                        self.CURRENT_SCOPE.VALUES[variable[0]][str(
                            dimensions)] = value
                    else:
                        self.CURRENT_SCOPE.add(
                            var_name[0], {str(dimensions): value})

            else:
                Error().name_error(var_name)

            # FIXME September 3, 2019: This does not work for BYREF values

            # for parameter in self.CURRENT_SCOPE.parameters:
                # if parameter[0].value == 'BYREF' and parameter[1] == var_name:
                #     if self.CURRENT_SCOPE.PARENT_SCOPE.VALUES.get(var_name) != None:
                #         self.CURRENT_SCOPE.PARENT_SCOPE.add(var_name, value)
                #     else:
                #         raise ReferenceError(repr(var_name))

    def visit_VariableName(self, node):
        return node.value

    def visit_VariableValue(self, node):
        var_name = node.value

        return self.check_declaration(var_name)

    # END: Variable Assignment

    # START: Array Assignment

    def visit_ElementName(self, node):
        var_name = self.visit(node.variable)
        indexes = []
        for index in node.indexes:
            indexes.append(self.visit(index))

        return [var_name, indexes]

    def visit_ElementValue(self, node):
        var_name = node.value

        indexes = []

        for index in node.indexes:
           indexes.append(self.visit(index))


        if self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name) is None:
            raise NameError(var_name)
        else:
            try:
                value = self.CURRENT_SCOPE.VALUES.get(var_name).get(str(indexes))
                return value
            except:
                raise UnboundLocalError(repr(var_name))


    def visit_Index(self, node):
        return self.visit(node.index)

    def visit_AssignArray(self, node):
        array = []

        for element in node.array:
            array.append(self.visit(element))

        return array

    # END: Array Assignment

    # START: Type Assignment

    def visit_TypeName(self, node):
        object_ = self.visit(node.object_)
        property_ = self.visit(node.property_)

        return [object_, property_]

    def visit_TypeValue(self, node):
        pass

    # END: Type Assignment

    # START: Input

    def visit_AssignInput(self, node):
        var_name = self.visit(node.input_node)
        value = input(node.input_node.input_string)

        if type(var_name) != list:
            type_ = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name)

            value = self.try_type(type_, value, var_name)

            self.CURRENT_SCOPE.add(var_name, value)

            # for parameter in self.CURRENT_SCOPE.parameters:
            #     if parameter[0].value == 'BYREF' and parameter[1] == var_name:
            #         if self.CURRENT_SCOPE.PARENT_SCOPE.VALUES.get(var_name) != None:
            #             self.CURRENT_SCOPE.PARENT_SCOPE.add(var_name, value)
            #         else:
            #             raise ReferenceError(repr(var_name))
        else:
            data_type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name[0])
            if data_type is not None:
                dimensions = var_name[1]

                # Checks if the number of dimensions(rank) of both arrays is the same
                if len(dimensions) != len(data_type.dimensions):
                    Error().index_error(var_name)

                # Checks if the index is within upper and lower bound limits
                for i in range(len(dimensions)):
                    if dimensions[i] < data_type.dimensions[i][0] or dimensions[i] > data_type.dimensions[i][1]:
                        Error().index_error(var_name[0])

                    type_ = data_type.data_type

                    self.try_type(type_, value, var_name)

                    if self.CURRENT_SCOPE.VALUES.get(var_name[0]):
                        self.CURRENT_SCOPE.VALUES[var_name[0]][str(dimensions)] = value
                    else:
                        self.CURRENT_SCOPE.add(var_name[0], {str(dimensions) : value})

    def visit_Input(self, node):
        return self.visit(node.variable)

    # END: Input

    # START: Output

    def visit_Output(self, node):
        print(self.visit(node.output))

    # END: Output

    # START: Logical

    def visit_BinaryLogicalOperation(self, node):
        if node.logical_operation.value == 'AND':
            left = self.visit(node.left)
            right = self.visit(node.right)
            return left and right
        elif node.logical_operation.value == 'OR':
            left = self.visit(node.left)
            right = self.visit(node.right)
            return left or right
    def visit_UnaryLogicalOperation(self, node):
            return not self.visit(node.condition)

    def visit_Condition(self, node):
        comparison = node.comparison.value

        if comparison == '=':
            right = self.visit(node.right)
            if isinstance(right, list):
                return self.visit(node.left) in right
            else:
                return self.visit(node.left) == right
        elif comparison == '<':
            return self.visit(node.left) < self.visit(node.right)
        elif comparison == '>':
            return self.visit(node.left) > self.visit(node.right)
        elif comparison == '<=' or comparison == '=<':
            return self.visit(node.left) <= self.visit(node.right)
        elif comparison == '>=' or comparison == '=>':
            return self.visit(node.left) >= self.visit(node.right)
        elif comparison == '<>':
            return self.visit(node.left) != self.visit(node.right)

    # END: Logical

    # START: Selection

    def visit_Selection(self, node):
        for selection in node.selection_list:
            node, is_true = self.visit(selection)
            if is_true == True:
                return node

    def visit_SelectionStatement(self, node):
        if node.condition is not None:
            condition_result = self.visit(node.condition)
            if condition_result == True:
                return self.visit(node.block), True
            else:
                return None, False
        else:
            return self.visit(node.block), True

    # END: Selection

    # START: Case

    def visit_Case(self, node):
        for case in node.case_list:
            block, is_true = self.visit(case)
            if is_true == True:
                return block

    def visit_Options(self, node):
        options = []
        for option in node.options:
            options.append(self.visit(option))

        return options

    def visit_Range(self, node):
        return range(self.visit(node.start), self.visit(node.end) + 1)

    # END: Case

    # START: Iteration

    def visit_Iteration(self, node):
        self.visit(node.assignment)
        variable = node.variable
        start = self.CURRENT_SCOPE.VALUES.get(self.visit(variable))
        var_name = node.variable.value
        end = self.visit(node.end)
        step = self.visit(node.step)
        value = start

        while value <= end:
            self.visit(node.block)
            self.CURRENT_SCOPE.VALUES[var_name] += step
            value = self.CURRENT_SCOPE.VALUES[var_name]

    # END: Iteration

    # START: Loop

    def visit_Loop(self, node):
        if node.loop_while == False:
            condition = False
        else:
            condition = self.visit(node.condition)

        while condition == node.loop_while:
            self.visit(node.block)
            condition = self.visit(node.condition)

    # END: Loop

    # START: Built-in Function

    def visit_BuiltInFunction(self, node):
        parameters = []
        for parameter in node.parameters:
            parameters.append(self.visit(parameter))

        node.parsed_parameters = parameters

        return self.visit_function(node)

    # END: Built-in Function

    # START: Procedure/Function

    def visit_FunctionCall(self, node):
        name = self.visit(node.name)
        scope = self.SCOPES.get(name)

        if scope != None:
            parameters = []
            for parameter in node.parameters:
                parameters.append(self.visit(parameter))

            scope.PARENT_SCOPE = self.CURRENT_SCOPE
            self.CURRENT_SCOPE = scope
            self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE

            if len(parameters) == len(self.CURRENT_SCOPE.parameters):
                for i in range(0, len(parameters)):
                    value = parameters[i]
                    reference_type = self.CURRENT_SCOPE.parameters[i][0]
                    var_name = self.CURRENT_SCOPE.parameters[i][1]

                    if reference_type == 'BYREF':
                        try:
                            parent_name = node.parameters[i].value
                        except:
                            Error().reference_error('A variable must be passed into BYREF')

                        self.CURRENT_SCOPE.SYMBOL_TABLE.SYMBOL_TABLE[var_name].parent_name = parent_name

                    type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name)
                    self.check_type(type, value, var_name)
                    self.CURRENT_SCOPE.add(var_name, parameters[i])

                return_value = self.visit(self.CURRENT_SCOPE.block)

                for parameter in self.CURRENT_SCOPE.parameters:
                    reference_type = parameter[0]
                    var_name = parameter[1]
                    if reference_type == 'BYREF':
                        current_value = self.CURRENT_SCOPE.VALUES.get(var_name)

                        parent_name = self.CURRENT_SCOPE.SYMBOL_TABLE.SYMBOL_TABLE[var_name].parent_name

                        self.CURRENT_SCOPE.PARENT_SCOPE.VALUES[parent_name] = current_value

                self.CURRENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE
                self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE



                if scope.return_type != None:
                    self.check_type(scope.return_type, return_value, var_name)
                    return return_value

            else:
                raise SyntaxError('Expected ' + str(len(self.CURRENT_SCOPE.parameters)) + ' parameter(s).' + ' Got ' + str(len(parameters)) + ' parameter(s)')
        else:
            Error().name_error('{} does not exist'.format(name))

    def visit_Function(self, node):
        name = self.visit(node.name)
        self.SCOPES[name] = Scope(self.CURRENT_SCOPE, [], self.visit(node.return_type), node.block)

        if node.return_type == None:
            self.CURRENT_SCOPE.SYMBOL_TABLE.add(name, 'PROCEDURE')
        else:
            self.CURRENT_SCOPE.SYMBOL_TABLE.add(name, 'FUNCTION')

        parameters = []

        for parameter in node.parameters:
            variable, data_type, reference_type = self.visit(parameter)
            metadata = Variable(data_type, None, reference_type)
            self.SCOPES[name].SYMBOL_TABLE.add(variable, metadata)
            self.SCOPES[name].parameters.append([reference_type, variable])

    def visit_Parameter(self, node):
        variable = self.visit(node.variable)
        data_type = self.visit(node.data_type)
        reference_type = node.reference_type.value

        return variable, data_type, reference_type

    # END: Procedure/Function

    # START: File

    def visit_File(self, node):
        file_name = self.visit(node.file_name)
        self.CURRENT_SCOPE.SYMBOL_TABLE.add(file_name, 'FILE')
        self.CURRENT_SCOPE.add(file_name, open(file_name, self.visit(node.file_mode)))

    def visit_FileMode(self, node):
        file_mode = node.file_mode.value
        if file_mode == 'READ':
            return 'r'
        elif file_mode == 'WRITE':
            return 'w'
        elif file_mode == 'APPEND':
            return 'a'

    def visit_ReadFile(self, node):
        file = self.visit(node.file_name)
        variable = self.visit(node.variable)
        type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(variable)
        if type != None:
            if type == 'STRING':
                try:
                    self.CURRENT_SCOPE.add(variable, file.readline())
                except:
                    Error().exception(file.name)
            else:
                Error().type_error(variable)
        else:
            Error().name_error(variable)

    def visit_WriteFile(self, node):
        file = self.visit(node.file_name)
        line = self.visit(node.line)
        try:
            file.write(line)
        except:
            Error().exception(file.name)

    def visit_CloseFile(self, node):
        file = self.visit(node.file_name)
        try:
            file.close()
            del self.CURRENT_SCOPE.VALUES[file.name]
        except:
            Error().exception(file.name)

    # END: File

    # START: Helper Functions

    def check_type(self, type, value, var_name):
        if type in self.CURRENT_SCOPE.DATA_TYPES:
            if not isinstance(value, self.CURRENT_SCOPE.DATA_TYPES[type]):
                Error().type_error(var_name)

    def try_type(self, type_, value, var_name):
        if type_ is not None:
            if type_ == 'INTEGER':
                try:
                    value = int(value)
                except:
                     Error().type_error(repr(var_name))
            if type_ == 'REAL':
                try:
                    value = float(value)
                except:
                     Error().type_error(repr(var_name))
            elif type_ == 'BOOLEAN':
                try:
                    value = bool(value)
                except:
                     Error().type_error(repr(var_name))
            elif type_ == 'STRING':
                try:
                    value = str(value)
                except:
                     Error().type_error(repr(var_name))
            elif type_ == 'CHAR':
                try:
                    value = str(value)
                    if len(value) != 1:
                         Error().type_error(repr(var_name))
                except:
                    Error().type_error(repr(var_name))

            return value


    def check_declaration(self, var_name):
        if self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name) is None:
            Error().name_error(var_name)
        else:
            try:
                value = self.CURRENT_SCOPE.VALUES.get(var_name)
                return value
            except:
                Error().unbound_local_error(var_name)

    # END: Helper Functions