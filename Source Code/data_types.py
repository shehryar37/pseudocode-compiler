from copy import copy
from error import Error


class DataType():
    def __init__(self, data_type, referee_name=None, reference_type="BYVAL"):
        self.data_type = data_type
        self.referee_name = referee_name
        self.reference_type = reference_type

# START: Variable


class VariableType(DataType):
    def __init__(self, data_type, referee_name=None, reference_type="BYVAL"):
        super().__init__(data_type, referee_name, reference_type)

    def declare(self, value=None):
        return Variable(value)


class Variable():
    def __init__(self, value):
        self.value = value

    def assign(self, value):
        self.value = value[0]

# END: Variable

# START: Constant


class ConstantType(DataType):
    def __init__(self, data_type='CONSTANT'):
        super().__init__(data_type)

    def declare(self, value=None):
        return Constant(value)


class Constant():
    def __init__(self, value):
        self.value = value

    def assign(self, value):
        self.value = value[0]

# END: Constant

# START: Array


class ArrayType(DataType):
    def __init__(self, dimensions, data_type, referee_name=None, reference_type="BYVAL"):
        super().__init__(data_type, referee_name, reference_type)
        self.dimensions = dimensions

    def declare(self):
        layers = len(self.dimensions)
        layer_indexes = {}
        previous_layer_indexes = {}

        for i in range(layers - 1, -1, -1):
            if i + 1 == layers:
                for j in range(self.dimensions[i][0], self.dimensions[i][1] + 1):
                    layer_indexes[j] = None
            else:
                previous_layer_indexes = copy(layer_indexes)
                layer_indexes = {}

                for j in range(self.dimensions[i][0], self.dimensions[i][1] + 1):
                    layer_indexes[j] = previous_layer_indexes

        return Array(layer_indexes)


class Array():
    def __init__(self, value):
        self.value = value

    def assign(self, data):
        value = data[0]
        indexes = data[1]

        array_indexes = self.value

        for i in range(len(indexes) - 1):
            try:
                array_indexes = array_indexes.get(indexes[i])
            except:
                # TODO November 07, 2019: Find a way to output the name of the array
                Error().index_error('Index out of bounds')

        array_indexes[indexes[-1]] = value

# END: Array

# START: Type


class TypeType(DataType):
    def __init__(self, scope, data_type, referee_name=None, reference_type="BYVAL"):
        super().__init__(data_type, referee_name, reference_type)
        self.scope = scope


class Type():
    pass

    # END: Type
