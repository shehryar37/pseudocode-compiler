from symbol_table import SymbolTable
from copy import deepcopy


class Scope():
    def __init__(self, PARENT_SCOPE=None, block=None, parameters=[], return_type=[]):
        """Initializes a Scope object

        Keyword Arguments:
            PARENT_SCOPE {Scope} -- The scope in which this object will be created in (default: {None})
            block {Block} -- All the statements within this Scope object (default: {None})
            parameters {[[str]]} -- The names, data types and reference types of all parameters (default: {[]})
            return_type {DataType} -- The type of value that will be returned (default: {[]})
        """
        self.SYMBOL_TABLE = SymbolTable()
        self.PARENT_SCOPE = PARENT_SCOPE
        self.parameters = parameters
        self.block = block
        self.return_type = return_type
        self.DATA_TYPES = {}
        self.USER_DEFINED_DATA_TYPES = {}
        self.init_data_types()
        self.VALUES = {}

        if self.PARENT_SCOPE != None:
            # Copy DATA_TYPES and VALUES from the parent scope
            self.DATA_TYPES = deepcopy(self.PARENT_SCOPE.DATA_TYPES)
            self.VALUES = deepcopy(self.PARENT_SCOPE.VALUES)

    def declare(self, name, metadata):
        """Adds an instance to SYMBOL_TABLE

        Arguments:
            name {str} -- The name of the instance
            metadata {Class(DataType)} -- The DataType of the instance
        """
        self.SYMBOL_TABLE.add(name, metadata)

    def assign(self, variable_name, *data):
        """Assigns to an instance in VALUES

        Arguments:
            variable_name {str} -- The name of the variable
            *data {list} -- The value (+indexes/property) of the instance
        """

        if self.VALUES.get(variable_name) is None:
            # Set the instance of variable_name in VALUES to None
            self.VALUES[variable_name] = data[0]
        else:
            # Set the instance of variable_name in VALUES to data[0]
            self.VALUES[variable_name].assign(data)

    def get(self, variable_name):
        """Fetches the value of an instance stored inside VARIABLES

        Arguments:
            variable_name {str} -- The name of the variable

        Returns:
            [type] -- [description]
        """
        if self.VALUES.get(variable_name) is not None:
            return self.VALUES.get(variable_name).value
        else:
            return None

    def init_data_types(self):
        self.DATA_TYPES['INTEGER'] = int
        self.DATA_TYPES['STRING'] = str
        self.DATA_TYPES['REAL'] = float
        self.DATA_TYPES['BOOLEAN'] = bool
        self.DATA_TYPES['CHAR'] = str

    def clear(self):
        self.VALUES = None
        self.parameters = None
