from function import BuiltInFunction
from scope import Scope
from error import Error
from symbol_table import *
from copy import deepcopy


class Interpreter():
    def __init__(self, parser):
        self.parser = parser
        self.SCOPES = {}
        self.PARENT_SCOPE = None
        self.SCOPES['GLOBAL'] = Scope(self.PARENT_SCOPE, None)
        self.CURRENT_SCOPE = self.SCOPES.get('GLOBAL')

    def interpret(self):
        tree = self.parser.block(['EOF'])
        self.visit(tree)

    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.visit_error)
        return visitor(node)

    def visit_error(self, node):
        Error().exception('No visit_{} method'.format(type(node).__name__))

    def visit_function(self, node):
        method_name = node.name.value
        visitor = getattr(BuiltInFunction(self.CURRENT_SCOPE),
                          method_name, self.visit_error)
        return visitor(node.parsed_parameters)

    def visit_Block(self, node):
        for statement in node.block:
            node = self.visit(statement)

            if node != None:
                return node

    def visit_Statement(self, node):
        return self.visit(node.statement)

    # START: Operation Handling

    def visit_BinaryOperation(self, node):

        operator = self.visit(node.operator)

        if operator == '+':
            return self.visit(node.left) + self.visit(node.right)
        elif operator == '-':
            return self.visit(node.left) - self.visit(node.right)
        elif operator == '*':
            return self.visit(node.left) * self.visit(node.right)
        elif operator == '^':
            return self.visit(node.left) ** self.visit(node.right)
        elif operator in ['/', 'DIV', 'MOD']:
            right = self.visit(node.right)

            if right == 0:
                Error().zero_error()

            if operator == '/':
                return self.visit(node.left) / right
            elif operator == 'DIV':
                return self.visit(node.left) // right
            elif operator == 'MOD':
                return self.visit(node.left) % right

    def visit_UnaryOperation(self, node):
        operator = self.visit(node.operator)

        if operator == '+':
            return +self.visit(node.expression)
        elif operator == '-':
            return -self.visit(node.expression)

    def visit_Operator(self, node):
        return node.value

    def visit_Value(self, node):
        return node.token.value

    # END: Operation Handling

    # START: Constants

    def visit_ConstantDeclaration(self, node):
        constant_name = self.visit(node.constant)
        value = self.visit(node.value)

        constant_metadata = ConstantType(value)
        self.CURRENT_SCOPE.declare(constant_name, constant_metadata)
        self.CURRENT_SCOPE.assign(constant_name, constant_metadata.declare(value))

    # END: Constants

    # START: Variable Declaration

    def visit_Declarations(self, declarations):
        for declaration in declarations.declarations:
            self.visit(declaration)

    def visit_Declaration(self, declaration):
        name = self.visit(declaration.variable)
        metadata = self.visit(declaration.data_type)

        self.CURRENT_SCOPE.declare(name, metadata)
        self.CURRENT_SCOPE.assign(name, metadata.declare())

    def visit_DataType(self, data_type):
        data_type = data_type.value

        if data_type in self.CURRENT_SCOPE.DATA_TYPES.keys():
            return VariableType(data_type)
        else:
            Error().type_error('TYPE {} has not been initialized'.format(data_type))

    # END: Variable Declaration

    # START: Array Declaration

    def visit_Array(self, node):
        data_type = self.visit(node.data_type).data_type
        dimensions = self.visit(node.dimensions)

        return ArrayType(dimensions, data_type)

    def visit_Dimensions(self, dimensions):
        dimension_list = []
        for dimension in dimensions.dimensions:
            dimension_list.append(self.visit(dimension))

        return dimension_list

    def visit_Dimension(self, dimension):

        lower_bound = self.visit(dimension.lower_bound)
        upper_bound = self.visit(dimension.upper_bound)

        if upper_bound < lower_bound:
            Error().index_error('Upper bound cannot be lesser than or equal to lower bound')

        return [lower_bound, upper_bound]

    def visit_Bound(self, bound):
        return self.visit(bound.value)

    # END: Array Declaration

    # START: Type Declaration

    def visit_TypeDeclaration(self, node):
        type_name = self.visit(node.type_name)

        # Creates a new scope with the TYPE name
        self.SCOPES[type_name] = scope = Scope(self.CURRENT_SCOPE, node.block)

        # Scopes into TYPE
        scope.PARENT_SCOPE = self.CURRENT_SCOPE
        self.CURRENT_SCOPE = scope
        self.PARENT_SCOPE = scope.PARENT_SCOPE

        self.visit(scope.block)

        # Gets all the declarations within TYPE
        children = {'SYMBOL_TABLE': self.CURRENT_SCOPE.SYMBOL_TABLE}

        # Scopes out of TYPE
        self.CURRENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE
        self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE

        self.CURRENT_SCOPE.DATA_TYPES[type_name] = type(
            type_name, (), children)

    # END: Type Declaration

    # START: Variable Assignment

    def visit_Assignment(self, node):
        name = self.visit(node.variable)
        value = self.visit(node.expression)

        if type(name) is not list:
            metadata = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(name)
            if type(metadata) == VariableType:
                self.check_type(metadata.data_type, value, name)
                self.CURRENT_SCOPE.assign(name, value)
            elif type(metadata) == ConstantType:
                Error().name_error('Cannot assign to CONSTANT')
            elif type(metadata) == ArrayType:
                # Figure this out later
                pass
            else:
                Error().unbound_local_error(name)
        elif type(name) is list:
            metadata = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(name[0])
            if type(metadata) == ArrayType:
                indexes = name[1]
                name = name[0]

                self.CURRENT_SCOPE.assign(name, value, indexes)

    def visit_VariableName(self, node):
        name = node.value

        return name

    def visit_VariableValue(self, node):
        name = node.value

        return self.check_declaration(name)

    # END: Variable Assignment

    # START: Array Assignment

    def visit_ElementName(self, node):

        indexes = []
        for index in node.indexes:
            indexes.append(self.visit(index))

        return [node.value, indexes]

    def visit_ElementValue(self, node):
        name = node.value

        indexes = []

        for index in node.indexes:
           indexes.append(self.visit(index))


        if self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(name) is None:
            raise NameError(name)
        else:
            try:
                value = self.CURRENT_SCOPE.get(name)
                for index in indexes:
                    value = value.get(index)

                return value
            except:
                raise Error().index_error(name)


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
        object_name = self.visit(node.object_name)
        property_name = self.visit(node.property_name)

        if getattr(node, 'assign_value', None) == None:
            return object_name

        value = self.visit(node.assign_value)
        delattr(node, 'assign_value')

        if type(object_name) == list:
            pass
        else:
            type_name = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(object_name)

            if type_name is not None:
                data_type = self.CURRENT_SCOPE.DATA_TYPES[type_name]
            else:
                Error().unbound_local_error(object_name)

            if data_type.SYMBOL_TABLE.lookup(property_name) is not None:

                if self.CURRENT_SCOPE.VALUES.get(object_name) is None:
                    self.CURRENT_SCOPE.add(object_name, {property_name: value})
                else:
                    self.CURRENT_SCOPE.VALUES[object_name][property_name] = value
            else:
                Error().name_error('{}.{} does not exist'.format(object_name, property_name))

    def visit_TypeValue(self, node):
        object_name = self.visit(node.object_name)
        property_name = self.visit(node.property_name)

        if self.CURRENT_SCOPE.VALUES.get(object_name) is not None:
            if property_name in self.CURRENT_SCOPE.VALUES[object_name].keys():
                return self.CURRENT_SCOPE.VALUES[object_name][property_name]
        else:
            Error().unbound_local_error(object_name)

    # END: Type Assignment

    # START: Input

    def visit_AssignInput(self, node):
        variable_name = self.visit(node.input_node)
        value = input(node.input_node.input_string)

        if type(variable_name) != list:
            type_ = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(variable_name)

            value = self.try_type(type_, value, variable_name)

            self.CURRENT_SCOPE.add(variable_name, value)
        else:
            data_type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(variable_name[0])
            if data_type is not None:
                dimensions = variable_name[1]

                # Checks if the number of dimensions(rank) of both arrays is the same
                if len(dimensions) != len(data_type.dimensions):
                    Error().index_error(variable_name)

                # Checks if the index is within upper and lower bound limits
                for i in range(len(dimensions)):
                    if dimensions[i] < data_type.dimensions[i][0] or dimensions[i] > data_type.dimensions[i][1]:
                        Error().index_error(variable_name[0])

                    type_ = data_type.data_type

                    self.try_type(type_, value, variable_name)

                    if self.CURRENT_SCOPE.VALUES.get(variable_name[0]):
                        self.CURRENT_SCOPE.VALUES[name[0]][str(dimensions)] = value
                    else:
                        self.CURRENT_SCOPE.add(variable_name[0], {str(dimensions) : value})

    def visit_Input(self, node):
        return self.visit(node.variable)

    # END: Input

    # START: Output

    def visit_Output(self, node):
        output = self.visit(node.output)
        if output is not None:
            print(output)

    # END: Output

    # START: Logical

    def visit_BinaryLogicalOperation(self, node):
        logical_operator = self.visit(node.logical_operator)

        if logical_operator == 'AND':
            left = self.visit(node.left)
            right = self.visit(node.right)
            return left and right
        elif logical_operator == 'OR':
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
        name = self.visit(node.variable)
        start = self.CURRENT_SCOPE.get(name)
        end = self.visit(node.end)
        step = self.visit(node.step)
        value = start

        while value <= end:
            self.visit(node.block)
            value = self.CURRENT_SCOPE.get(name) + step
            self.CURRENT_SCOPE.assign(name, value)

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
        scope = deepcopy(self.SCOPES.get(name))

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
                    name = self.CURRENT_SCOPE.parameters[i][1]

                    if reference_type == 'BYREF':
                        try:
                            parent_name = node.parameters[i].value
                        except:
                            Error().reference_error('A variable must be passed into BYREF')

                        self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(name).parent_name = parent_name

                    type = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(name)
                    self.check_type(type, value, name)
                    self.CURRENT_SCOPE.add(name, parameters[i])

                return_value = self.visit(self.CURRENT_SCOPE.block)

                for parameter in self.CURRENT_SCOPE.parameters:
                    reference_type = parameter[0]
                    name = parameter[1]
                    if reference_type == 'BYREF':
                        current_value = self.CURRENT_SCOPE.VALUES.get(name)

                        parent_name = self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(name).parent_name

                        self.CURRENT_SCOPE.PARENT_SCOPE.assign(parent_name, current_value)

                self.CURRENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE
                self.PARENT_SCOPE = self.CURRENT_SCOPE.PARENT_SCOPE

                if scope.return_type != None:
                    self.check_type(scope.return_type, return_value, name)
                    return return_value

            else:
                raise SyntaxError('Expected ' + str(len(self.CURRENT_SCOPE.parameters)) + ' parameter(s).' + ' Got ' + str(len(parameters)) + ' parameter(s)')
        else:
            Error().name_error('{} does not exist'.format(name))

    def visit_Function(self, node):
        name = self.visit(node.name)
        self.SCOPES[name] = Scope(self.CURRENT_SCOPE, node.block, return_type=node.return_type)

        if node.return_type == None:
            self.CURRENT_SCOPE.SYMBOL_TABLE.add(name, 'PROCEDURE')
        else:
            self.CURRENT_SCOPE.SYMBOL_TABLE.add(name, 'FUNCTION')

        parameters = []

        # TODO November 04, 2019: This will probably need to be updated
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
        self.CURRENT_SCOPE.SYMBOL_TABLE.add(file_name, Variable('FILE'))
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
            file.write(line + '\n')
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

    def check_type(self, type, value, name):
        if type in self.CURRENT_SCOPE.DATA_TYPES:
            if not isinstance(value, self.CURRENT_SCOPE.DATA_TYPES[type]):
                Error().type_error(name)

    def try_type(self, type_, value, name):
        if type_ is not None:
            if type_ in self.CURRENT_SCOPE.DATA_TYPES.keys():
                type_ = self.CURRENT_SCOPE.DATA_TYPES[type_]
            try:
                return type_(value)
            except:
                Error().type_error(repr(name))

    def check_declaration(self, name):
        if self.CURRENT_SCOPE.SYMBOL_TABLE.lookup(name) is None:
            Error().name_error(name)

        try:
            value = self.CURRENT_SCOPE.get(name)

            if value is None:
                Error().unbound_local_error(name)

            return value
        except:
            Error().unbound_local_error(name)

    # END: Helper Functions
