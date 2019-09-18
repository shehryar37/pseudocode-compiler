from function import BuiltInFunction
from scope import Scope
from arrays import Array

class Interpreter():
    def __init__(self, parser):
        self.parser = parser
        self.SCOPES = {}
        self.PARENT_SCOPE = None
        self.SCOPES['GLOBAL'] = Scope(self.PARENT_SCOPE, [], None, None)
        self.CURRENT_SCOPE = self.SCOPES.get('GLOBAL')

    def interpret(self):
        tree = self.parser.block(['EOF'])
        self.parser.check_token('EOF')
        self.visit(tree)

    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))

    def visit_function(self, node):
        method_name = node.name.value
        visitor = getattr(BuiltInFunction(self.CURRENT_SCOPE),
                          method_name, self.generic_visit)
        return visitor(node.parsed_parameters)

    def check_type(self, type, value, var_name):
        if type in self.CURRENT_SCOPE.DATA_TYPES:
            if not isinstance(value, self.CURRENT_SCOPE.DATA_TYPES[type]):
                raise TypeError(repr(var_name))

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
        # TODO September 18, 2019: Handle string concatination

        if node.operation.value == '+':
            return self.visit(node.left) + self.visit(node.right)
        elif node.operation.value == '-':
            return self.visit(node.left) - self.visit(node.right)
        elif node.operation.value == '*':
            return self.visit(node.left) * self.visit(node.right)
        elif node.operation.value == '/':
            return self.visit(node.left) / self.visit(node.right)
        elif node.operation.value == 'DIV':
            return self.visit(node.left) // self.visit(node.right)
        elif node.operation.value == 'MOD':
            return self.visit(node.left) % self.visit(node.right)

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
        self.CURRENT_SCOPE.SYMBOL_TABLE.add(self.visit(
            declaration.variable), self.visit(declaration.data_type))

    def visit_Array(self, node):
        data_type = self.visit(node.data_type)
        dimensions = self.visit(node.dimensions)

        array = Array(dimensions, data_type)

        return array

    def visit_DataType(self, data_type):
        if data_type.value in self.CURRENT_SCOPE.DATA_TYPES.keys():
            return data_type.value
        else:
            raise TypeError('TYPE ' + data_type.value +
                            ' has not been initialized')

    def visit_Dimensions(self, dimensions):
        dimension_list = []
        for dimension in dimensions.dimensions:
            dimension_list.append(self.visit(dimension))

        return dimension_list

    def visit_Dimension(self, dimension):
        return [self.visit(dimension.lower_bound), self.visit(dimension.upper_bound)]

    def visit_Bound(self, bound):
        return self.visit(bound.value)

    # END: Variable Declaration

    # START: Variable Assignment

    def visit_Assignment(self, node):
        variable = self.visit(node.variable)
        value = self.visit(node.expression)

        if type(variable) is not list:
            data_type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(variable)
            if data_type is not None:
                self.check_type(data_type, value, variable)
                self.CURRENT_SCOPE.add(variable, value)
            else:
                raise NameError(repr(variable))
        else:
            data_type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(variable[0])
            if data_type is not None:
                self.check_type(data_type.data_type, value, variable[0])

                dimensions = variable[1]

                # Checks if the number of dimensions(rank) of both arrays is the same
                if len(dimensions) != len(data_type.dimensions):
                    raise IndexError(repr(variable[0]))

                # Checks if the index is within upper and lower bound limits
                for i in range(len(dimensions)):
                    if dimensions[i] < data_type.dimensions[i][0] or dimensions[i] > data_type.dimensions[i][1]:
                        raise IndexError(repr(variable[0]))


                    if self.CURRENT_SCOPE.VALUES.get(variable[0]):
                        self.CURRENT_SCOPE.VALUES[variable[0]][str(dimensions)] = value
                    else:
                        self.CURRENT_SCOPE.add(variable[0], {str(dimensions) : value})

            else:
                raise NameError(repr(variable))

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
        value = self.CURRENT_SCOPE.VALUES.get(var_name)

        if self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name) is None:
            if value is None:
                raise UnboundLocalError(repr(var_name))
        else:
            return value

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

        value = self.CURRENT_SCOPE.VALUES.get(var_name).get(str(indexes))

        if self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name) is None:
            if value is None:
                raise UnboundLocalError(repr(var_name))
        else:
            return value

    def visit_Index(self, node):
        return self.visit(node.index)

    # END: Variable Assignment

    # START: Input

    def visit_AssignInput(self, node):
        var_name = self.visit(node.input_node)
        value = input(node.input_node.input_string)

        if type(var_name) != list:
            type_ = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name)

            if type_ is not None:
                if type_ == 'INTEGER':
                    try:
                        value = int(value)
                    except:
                        raise TypeError(repr(var_name))
                if type_ == 'REAL':
                    try:
                        value = float(value)
                    except:
                        raise TypeError(repr(var_name))
                elif type_ == 'BOOLEAN':
                    try:
                        value = bool(value)
                    except:
                        raise TypeError(repr(var_name))
                elif type_ == 'STRING':
                    try:
                        value = str(value)
                    except:
                        raise TypeError(repr(var_name))
                elif type_ == 'CHAR':
                    try:
                        value = str(value)
                        if len(value) != 1:
                            raise(TypeError(repr(var_name)))
                    except:
                        raise TypeError(repr(var_name))

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
                    raise IndexError(repr(var_name[0]))

                # Checks if the index is within upper and lower bound limits
                for i in range(len(dimensions)):
                    if dimensions[i] < data_type.dimensions[i][0] or dimensions[i] > data_type.dimensions[i][1]:
                        raise IndexError(repr(var_name[0]))

                    type_ = data_type.data_type

                    if type_ is not None:
                        if type_ == 'INTEGER':
                            try:
                                value = int(value)
                            except:
                                raise TypeError(repr(var_name))
                        if type_ == 'REAL':
                            try:
                                value = float(value)
                            except:
                                raise TypeError(repr(var_name))
                        elif type_ == 'BOOLEAN':
                            try:
                                value = bool(value)
                            except:
                                raise TypeError(repr(var_name))
                        elif type_ == 'STRING':
                            try:
                                value = str(value)
                            except:
                                raise TypeError(repr(var_name))
                        elif type_ == 'CHAR':
                            try:
                                value = str(value)
                                if len(value) != 1:
                                    raise(TypeError(repr(var_name)))
                            except:
                                raise TypeError(repr(var_name))

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
            return self.visit(node.left) and self.visit(node.right)
        elif node.logical_operation.value == 'OR':
            return self.visit(node.left) - self.visit(node.right)

    def visit_UnaryLogicalOperation(self, node):
            return not self.visit(node.condition)

    def visit_Condition(self, node):
        comparison = node.comparison.value

        if comparison == '=':
            return self.visit(node.left) in self.visit(node.right)
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

    def visit_Parameter(self, node):
        variable = self.visit(node.variable)
        data_type = self.visit(node.data_type)
        scope_type = node.scope_type

        return variable, data_type, scope_type

    # START: Procedure/Function

    def visit_Call(self, node):
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
                # TODO September 17, 2019: Try using foreach over here
                for i in range(0, len(parameters)):
                    value = parameters[i]
                    var_name = self.CURRENT_SCOPE.parameters[i][1]
                    type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(var_name)
                    self.check_type(type, value, var_name)
                    self.CURRENT_SCOPE.add(var_name, parameters[i])

                return_value = self.visit(self.CURRENT_SCOPE.block)

                for parameter in self.CURRENT_SCOPE.parameters:
                    scope_type = parameter[0]
                    variable = parameter[1]
                    # Figure this out
                    if scope_type == 'BYREF':
                        current_value = self.CURRENT_SCOPE.VALUES.get(variable)
                        reference_variable = self.CURRENT_SCOPE.PARENT_SCOPE.VALUES.get(variable)

                        if reference_variable != None:
                            self.CURRENT_SCOPE.PARENT_SCOPE.VALUES[variable] = current_value
                        else:
                            raise ReferenceError(variable)

                # self.CURRENT_SCOPE.VALUES.clear()
                # self.CURRENT_SCOPE.SYMBOL_TABLE.clear()

                self.CURRENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE
                self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE

                if scope.return_type != None:
                    self.check_type(self.visit(scope.return_type), return_value, var_name)
                    return return_value

            else:
                raise SyntaxError('Expected ' + str(len(self.CURRENT_SCOPE.parameters)) + ' parameter(s).' + ' Got ' + str(len(parameters)) + ' parameter(s)')
        else:
            raise NameError(name + ' does not exist')

    def visit_Function(self, node):
        name = self.visit(node.name)
        self.SCOPES[name] = Scope(self.CURRENT_SCOPE, [], node.return_type, node.block)


        if node.return_type == None:
            self.CURRENT_SCOPE.SYMBOL_TABLE.add(name, 'PROCEDURE')
        else:
            self.CURRENT_SCOPE.SYMBOL_TABLE.add(name, 'FUNCTION')

        parameters = []

        for parameter in node.parameters:
            variable, data_type, scope_type = self.visit(parameter)
            self.SCOPES[name].SYMBOL_TABLE.add(variable, data_type)
            self.SCOPES[name].parameters.append([scope_type, variable])

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
                    raise Exception(file.name)
            else:
                raise TypeError(repr(variable))
        else:
            raise NameError(repr(variable))


    def visit_WriteFile(self, node):
        file = self.visit(node.file_name)
        line = self.visit(node.line)
        try:
            file.write(line)
        except:
            raise Exception(file.name)

    def visit_CloseFile(self, node):
        file = self.visit(node.file_name)
        try:
            file.close()
            del self.CURRENT_SCOPE.VALUES[file.name]
        except:
            raise Exception(file.name)

    # END: File

    # START: Type Declaration

    # def visit_TypeDeclaration(self, node):
    #     type_name = self.visit(node.type_name)

    #     self.SCOPES[type_name] = scope = Scope(self.CURRENT_SCOPE, [], [], node.block)

    #     scope.PARENT_SCOPE = self.CURRENT_SCOPE
    #     self.CURRENT_SCOPE = scope
    #     self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE

    #     self.visit(scope.block)

    #     children = {'SYMBOL_TABLE' : self.CURRENT_SCOPE.SYMBOL_TABLE}

    #     for variable in scope.SYMBOL_TABLE.SYMBOL_TABLE.keys():
    #         children[variable] = None

    #     self.CURRENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE
    #     self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE

    #     self.CURRENT_SCOPE.DATA_TYPES[type_name] = type(type_name, (), children)

    # def visit_TypeAssignment(self, node):
    #     object = self.visit(node.object)

    # END: Type Declaration
