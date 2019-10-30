class Variable():
    def __init__(self, var_type, parent_name=None, var_reference="BYVAL"):
        self.var_type = var_type
        self.parent_name = parent_name
        self.var_reference = var_reference


class Constant():
    def __init__(self, constant):
        self.constant = constant
        self.var_type = 'CONSTANT'

    # Not currently being used
    @property
    def get(self):
        return self.constant


class Array():
    def __init__(self, dimensions, data_type):
        self.dimensions = dimensions
        self.data_type = data_type


class Type():
    def __init__(self, object_, property_):
        self.object_ = object_
        self.property = property_
